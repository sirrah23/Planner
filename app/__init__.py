from flask import Flask, render_template, abort
from flask_restful import Resource, Api
from flask_pymongo import PyMongo
import os

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
    
    #TODO: Class level collection variable

    @classmethod
    def get_plan_from_link(cls, link): #TODO: Rename
        result = mongo.db.plans.find_one({"link": link})
        if not result:
            return None
        else:
            return Plan(
                        obj_id = result["_id"],
                        link=result["link"],
                        items=result["items"],
                        groups=result["groups"]
                    )

    @classmethod
    def insert(self, p):
        #TODO: link already exists...
        result = mongo.db.plans.insert_one(
            {
                "link": p.link,
                "items": p.items,
                "groups": p.groups
            })
        return result.inserted_id


class Planner(Resource):
    def get(self, plan_link):
        data = PlansRepo.get_plan_from_link(plan_link)
        if not data:
            abort(404)
        else:
            res = {
                    "link": data.link,
                    "items": data.items,
                    "groups": data.groups
            }
            return res


api.add_resource(Planner, '/api/planner/<string:plan_link>')

@app.route('/<plan_link>')
def main(plan_link):
    data = PlansRepo.get_plan_from_link(plan_link)
    if data:
        return render_template('main.html')
    else:
        abort(404)
