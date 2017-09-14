import os
import json
from app.models.models import PlansRepo, LinkRepo, ItemRepo, GroupRepo
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


p_repo = PlansRepo(app, mongo)
l_repo = LinkRepo(app, mongo)
i_repo = ItemRepo(app, mongo)
g_repo = GroupRepo(app, mongo)

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

        # Delete the item!
        app.logger.info("Starting item deletion")
        deleted_count = i_repo.delete_item(_id)
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

    def delete(self, link, _id):
        # Grab arguments from request
        app.logger.info("Delete group at " + link)
        app.logger.info("Group to delete is " + _id) 

        # Delete the group!
        app.logger.info("Starting group deletion")
        deleted_count = g_repo.delete_group(_id, i_repo)
        return deleted_count, 201


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
