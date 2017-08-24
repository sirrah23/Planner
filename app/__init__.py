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

    def insert(self, p=None):
        #TODO: link already exists...
        if not p:
            link = self.generate_link()
            while self.get_plan_from_link(link):
                link = self.generate_link()
            to_insert = Plan(link)
        else:
            link = p.link
            to_insert = p
        result = self.conn.db.plans.insert_one({
            "link": to_insert.link,
            "items": to_insert.items,
            "groups": to_insert.groups
        })
        return link

    def update(self, link, data):
        #TODO: Have a validator object validate data
        res = self.conn.db.plans.update_one({"link": link}, {"$set": data})
        return res.modified_count == 1

p_repo = PlansRepo(mongo)


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

    def patch(self, link):
        app.logger.info('Attempting to patch on ' + link)
        parser = reqparse.RequestParser().add_argument('data')
        args = parser.parse_args()
        patch_data = json.loads(args.data)
        p_repo.update(link, patch_data)
        app.logger.info(link + " has been updated with " + str(patch_data))
        return 201

    def post(self):
        app.logger.info('Attempting to post planner')
        new_link = p_repo.insert()
        app.logger.info(new_link + " has been created")
        return {"link": new_link}, 201


class Item(Resource):
    pass


class Group(Resource):
    pass


api.add_resource(Planner, '/api/v1/planner', '/api/v1/planner/<string:link>')
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
