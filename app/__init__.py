from flask import Flask, render_template, abort
from flask_restful import Resource, Api, reqparse
from flask_pymongo import PyMongo
import os
import json
import random
import string
from collections import namedtuple

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
        result = self.conn.db.plans.find_one({"link": link})
        if not result:
            return None
        else:
            return Plan(
                        obj_id = result["_id"],
                        link=result["link"],
                        items=result["items"],
                        groups=result["groups"]
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

    def get(self, plan_link):
        data = p_repo.get_plan_from_link(plan_link)
        if not data:
            abort(404)
        else:
            res = {
                    "link": data.link,
                    "items": data.items,
                    "groups": data.groups
            }
            return res

    def patch(self, plan_link):
        app.logger.info('Attempting to patch on ' + plan_link)
        parser = reqparse.RequestParser().add_argument('data')
        args = parser.parse_args()
        patch_data = json.loads(args.data)
        p_repo.update(plan_link, patch_data)
        app.logger.info(plan_link + " has been updated with " + str(patch_data))
        return 201

class PlannerCollection(Resource):

    def post(self):
        app.logger.info('Attempting to post')
        p_repo.update(plan_link, patch_data)
        app.logger.info(plan_link + " has been updated with " + str(patch_data))
        return 201

api.add_resource(PlannerCollection, '/api/planner')
api.add_resource(Planner, '/api/planner/<string:plan_link>')

@app.route('/<plan_link>')
def main(plan_link):
    app.logger.info('Attempting to obtain link ' + plan_link)
    data = p_repo.get_plan_from_link(plan_link)
    if data:
        return render_template('main.html')
    else:
        abort(404)
