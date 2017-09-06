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
        block_end_string='%>', variable_start_string='%%',
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

    #TODO: Rename
    #TODO: Can this method be simplified/split up?
    #TODO: Use some of the other repositories?
    def get_plan_from_link(self, link): 
        app.logger.info("Reading link from database")
        link_data = self.conn.db.links.find_one({"link":link})
        if not link_data:
            return None
        app.logger.info("Link found - getting items and groups")
        link_id = link_data["_id"]
        pipeline = [
            {"$match": {"link": link_id}},
            {"$lookup":{"from":"groups", "localField":"group", "foreignField":"_id", "as":"group"}},
            {"$project":{"_id":1, "checked":1, "name":1, "group":{"$let":{"vars":{"field":{"$arrayElemAt":["$group",0]}},"in": "$$field.name"}}}},
        ]
        result = self.conn.db.items.aggregate(pipeline)
        if not result:
            app.logger.info("Empty data - returning plan")
            return Plan(
                        link=link,
                        items=[],
                        groups= {}
                    )
        app.logger.info("Building items + groups into plan")
        planner = {}
        planner["link"] = link
        planner["items"] = []
        planner["groups"] = {}
        for r in result:
            r["_id"] = str(r["_id"])
            if "group" in r:
                if r["group"] not in planner["groups"]:
                    planner["groups"][r["group"]] = {"items": []}
                planner["groups"][r["group"]]["items"] += [r]
            else:
                planner["items"] += [r]
        group_data = self.conn.db.groups.find({"link": link_id})
        for g in group_data:
            if g["name"] not in planner["groups"]:
                planner["groups"][g["name"]] = {"_id":str(g["_id"]), "items":[]}
            else:
                planner["groups"][g["name"]]["_id"] = str(g["_id"])
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

    def update_item(self, item_id, link_id, data):
        app.logger.info('Attempting to update item ' + item_id + " with data " + str(data))
        updated_fields = {}
        for k, v in data.items():
            if k == "group":
                updated_fields[k] = ObjectId(v)
            else:
                updated_fields[k] = v
        item_objid = ObjectId(item_id)
        link_objid = ObjectId(link_id)
        return self.conn.db.items.update_one({"_id": item_objid, "link": link_objid}, {"$set": updated_fields}, upsert=False).modified_count

    def delete_item(self, item_id):
        app.logger.info('Starting delete for item with ObjectId: ' + str(item_id))
        return self.conn.db.items.delete_one({"_id": item_id}).deleted_count

    def get_items_by_group_id(self, group_id):
        app.logger.info('Getting items for group: ' + group_id)
        items = self.conn.db.items.find({"group": ObjectId(group_id)})
        return list(map(lambda i: str(i["_id"]), items))


class GroupRepo(object):

    def __init__(self, conn):
        self.conn = conn

    def create_group(self, name, link_id):
        app.logger.info('Attempting to create group with name ' + name)
        link_id_text = str(link_id)
        app.logger.info('Link for group creation is ' + link_id_text)
        group_data_to_insert = {'name': name, 'link': link_id}
        inserted_id = self.conn.db.groups.insert_one(group_data_to_insert).inserted_id
        group_data_to_insert["_id"] = str(inserted_id)
        group_data_to_insert["link"] = link_id_text
        app.logger.info('Group was created ' + str(group_data_to_insert))
        return group_data_to_insert

p_repo = PlansRepo(mongo)
l_repo = LinkRepo(mongo)
i_repo = ItemRepo(mongo)
g_repo = GroupRepo(mongo)

class Planner(Resource):

    def get(self, link):
        app.logger.info("Get request for Planner resource: " + link)
        app.logger.info("Attempting to get data from Planner repo: " + link)
        data = p_repo.get_plan_from_link(link)
        if not data:
            abort(404)
        else:
            app.logger.info("Data retrieval successful for: " + link)
            app.logger.info(data)
            resp = {}
            resp["link"] = data.link
            resp["items"] = data.items
            resp["groups"] = data.groups
            return resp, 201


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

    def delete(self, link, _id):
        # Grab arguments from request
        app.logger.info("Delete item at " + link)
        app.logger.info("Item to delete is " + _id) 
        # Convert item string id into Object ID
        item_id = ObjectId(_id)

        # Delete the item!
        app.logger.info("Starting item deletion")
        deleted_count = i_repo.delete_item(item_id)
        return deleted_count, 201

    def patch(self, link, _id):
        app.logger.info("Patching item " + _id + " @ " + link)

        # Grab arguments from request
        app.logger.info("Parsing argument for patch")
        parser = reqparse.RequestParser()
        parser.add_argument('data')
        args = parser.parse_args()
        app.logger.info("Item patch arguments: " + str(args))

        # Convert argument to JSON
        args_json = json.loads(args.data)
        app.logger.info("Argument converted to JSON")

        # Get Object ID for link as it is the FK for items
        link_id = l_repo.get_obj_id_link(link)
        app.logger.info("Link ObjectID Obtained")

        # Finally patch the item!
        app.logger.info("Begin the item update")
        updated_count = i_repo.update_item(_id, link_id, args_json)
        return updated_count, 201

class Group(Resource):

    def post(self, link):
        # Grab arguments from request
        app.logger.info("Creating group at " + link)
        parser = reqparse.RequestParser()
        parser.add_argument('data')
        args = parser.parse_args()
        app.logger.info("Group creation arguments: " + str(args))

        # Convert argument to JSON
        args_json = json.loads(args.data)
        app.logger.info("Argument converted to JSON")

        # Get Object ID for link as it is the FK for groups
        link_id = l_repo.get_obj_id_link(link)
        app.logger.info("Link ObjectID Obtained")

        # Create the group!
        app.logger.info("Starting new group creation")
        new_group_data = g_repo.create_group(args_json['name'], link_id)
        return new_group_data, 201


api.add_resource(Link, '/api/v1/planner')
api.add_resource(Planner, '/api/v1/planner/<string:link>')
api.add_resource(Item, '/api/v1/planner/<string:link>/item', '/api/v1/planner/<string:link>/item/<string:_id>')
api.add_resource(Group, '/api/v1/planner/<string:link>/group', '/api/v1/planner/<string:link>/group/<string:_id>')

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
