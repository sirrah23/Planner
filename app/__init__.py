from flask import Flask, render_template
from flask_restful import Resource, Api
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
app.config.from_object('app.config.DevelopmentConfig') # TODO: Environment variable
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
    def get(self):
        return {
                    "items":["Tents","BBQ Sauce","Bug Spray"],
                    "groups":{
                        "H&M":[
                            {
                                "name": "Hot Sauce",
                                "checked": False
                            },
                            {
                                "name": "Sleeping Bags",
                                "checked": True
                            }
                        ],

                        "C&D":[
                            {
                                "name": "chicken",
                                "checked": True
                            }
                        ]
                    },
                }

api.add_resource(Planner, '/api/planner')

@app.route('/')
def index():
    return render_template('index.html')
