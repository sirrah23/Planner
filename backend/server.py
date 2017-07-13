from flask import Flask, render_template
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

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

api.add_resource(Planner, '/planner')


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
