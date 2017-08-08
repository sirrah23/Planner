from flask import Flask, render_template, abort
from flask_restful import Resource, Api, reqparse
from flask_pymongo import PyMongo
import os
import json

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

class Plan(object):

    def __init__(self, link, items=[], groups={}, obj_id=None):
        self.obj_id = obj_id
        self.link = link
        self.items = items
        self.groups = groups

class PlansRepo(object):
    
    def __init__(self, conn):
        self.conn = conn

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

    def insert(self, p):
        #TODO: link already exists...
        result = self.conn.db.plans.insert_one(
            {
                "link": p.link,
                "items": p.items,
                "groups": p.groups
            })
        return result.inserted_id

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

    def post(self, plan_link):
        app.logger.info('Attempting to post on ' + plan_link)
        parser = reqparse.RequestParser().add_argument('data')
        args = parser.parse_args()
        post_data = json.loads(args.data)
        p_repo.update(plan_link, post_data)
        app.logger.info(plan_link + " has been updated with " + str(post_data))
        return 201


api.add_resource(Planner, '/api/planner/<string:plan_link>')

@app.route('/<plan_link>')
def main(plan_link):
    app.logger.info('Attempting to obtain link ' + plan_link)
    data = p_repo.get_plan_from_link(plan_link)
    if data:
        return render_template('main.html')
    else:
        abort(404)
