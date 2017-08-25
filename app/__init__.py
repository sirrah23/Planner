import os
import json
import random
import string
from bson import ObjectId
from collections import namedtuple
from flask import Flask, render_template, abort
from flask_restful import Resource, Api, reqparse
from flask_pymongo import PyMongo

class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='%%',
        variable_end_string='%%',
        comment_start_string='<#',
        comment_end_string='#>',
))

app = CustomFlask(__name__)
app.config.from_object(os.environ.get('APP_CONFIG'))
api = Api(app)
mongo = PyMongo(app)

class Plan(namedtuple('Plan', ['obj_id', 'link', 'items', 'groups'])):
    """Wrapper to override constructor so that this named tuple 
    can be given default arguments."""

    def __new__(cls, link, obj_id=None, items=[], groups={}):
        return super(Plan, cls).__new__(cls, obj_id, link, items, groups)

class PlansRepo(object):
    
    def __init__(self, conn):
        self.conn = conn

    #TODO: Move
    def generate_link(self, l=10):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(l))

    def get_plan_from_link(self, link): #TODO: Rename
        link_data = self.conn.db.links.find_one({"link":link})
        if not link_data:
            return None
        link_id = link_data["_id"]
        pipeline = [
            {"$match": {"link": link_id}},
            {"$lookup":{"from":"groups", "localField":"group", "foreignField":"_id", "as":"group"}},
            {"$project":{"_id":1, "checked":1, "link":1, "name":1, "group":{"$let":{"vars":{"field":{"$arrayElemAt":["$group",0]}},"in": "$$field.name"}}}},
            {"$group": {"_id":"$group", "items":{"$push":"$$ROOT"}}}
        ]
        result = self.conn.db.items.aggregate(pipeline)
        if not result:
            return Plan(
                        link=link,
                        items=[],
                        groups= {}
                    )
        planner = {}
        planner["link"] = link
        planner["items"] = []
        planner["groups"] = {}
        for r in result:
            if not r["_id"]:
                planner["items"] = r["items"]
            else:
                planner["groups"][r["_id"]] = r["items"]
        group_data = self.conn.db.groups.find({"link":link_id})
        for g in group_data:
            if g["name"] not in planner["groups"]:
                planner["groups"][g["name"]] = []
        return Plan(
                    link=planner["link"],
                    items=planner["items"],
                    groups=planner["groups"]
                )

class LinkRepo(object):

    def __init__(self, conn):
        self.conn = conn

    def generate_link_text(self, l=10):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(l))

    def create_link(self):
        app.logger.info('Attempting to create a link')
        new_link_text = self.generate_link_text()
        app.logger.info('Link text generated ' + new_link_text)
        inserted_id = self.conn.db.links.insert_one({"link": new_link_text}).inserted_id
        app.logger.info('Link inserted with id ' + str(inserted_id))
        return {"_id": str(inserted_id), "link": new_link_text}

    def get_obj_id_link(self, link):
        return self.conn.db.links.find_one({"link":link})["_id"]


class ItemRepo(object):

    def __init__(self, conn):
        self.conn = conn

    def create_item(self, name, link_id, checked=False, group_id=""):
        app.logger.info('Attempting to create item with name ' + name)
        link_id_text = str(link_id)
        app.logger.info('Link for item creation is ' + link_id_text)
        item_data_to_insert = {'name': name,'checked': checked,'link': link_id,'group': group_id}
        inserted_id = self.conn.db.items.insert_one(item_data_to_insert).inserted_id
        item_data_to_insert["_id"] = str(inserted_id)
        item_data_to_insert["link"] = link_id_text
        app.logger.info('Item was created ' + str(item_data_to_insert))
        return item_data_to_insert


class GroupRepo(object):
    pass


p_repo = PlansRepo(mongo)
l_repo = LinkRepo(mongo)
i_repo = ItemRepo(mongo)

class Planner(Resource):

    def get(self, link):
        data = p_repo.get_plan_from_link(link)
        if not data:
            abort(404)
        else:
            res = {
                    "link": data.link,
                    "items": data.items,
                    "groups": data.groups
            }
            return res


class Link(Resource):

    def post(self):
        new_link_data = l_repo.create_link()
        app.logger.info('Sending new link back ' + str(new_link_data))
        return new_link_data, 201


class Item(Resource):

    def post(self, link):
        # Grab arguments from request
        app.logger.info("Creating item at " + link)
        parser = reqparse.RequestParser()
        parser.add_argument('data')
        args = parser.parse_args()
        app.logger.info("Item creation arguments: " + str(args))

        # Convert argument to JSON
        args_json = json.loads(args.data)
        app.logger.info("Argument converted to JSON")

        # Get Object ID for link as it is the FK for items
        link_id = l_repo.get_obj_id_link(link)
        app.logger.info("Link ObjectID Obtained")

        # Create the item!
        app.logger.info("Starting new item creation")
        new_item_data = i_repo.create_item(args_json['name'], link_id)
        return new_item_data, 201


class Group(Resource):
    pass


api.add_resource(Link, '/api/v1/planner')
api.add_resource(Planner, '/api/v1/planner/<string:link>')
api.add_resource(Item, '/api/v1/planner/<string:link>/item', '/api/v1/planner/<string:link>/item/:id')
api.add_resource(Group, '/api/v1/planner/<string:link>/group', '/api/v1/planner/<string:link>/group/:id')

@app.route('/')
def index():
    app.logger.info('Directing to index page')
    return render_template('index.html')

@app.route('/<link>')
def planner_app(link):
    app.logger.info('Attempting to obtain link ' + link)
    data = p_repo.get_plan_from_link(link)
    if data:
        return render_template('app.html')
    else:
        abort(404)
