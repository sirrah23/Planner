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

class Plans(object):

    @classmethod
    def get_plan_from_link(cls, link):
        result = mongo.db.plans.find_one({"link": link})
        if not result:
            return {"status": "fail", "errormsg": "Non-existent link", "data": {}}
        else:
            return {"status": "success", "errormsg": "", "data": result}


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
    mongo.db.plans.insert({"link":"abcdef", "items":["a", "b", "c"], "groups": {}}) #temp
    return render_template('index.html')