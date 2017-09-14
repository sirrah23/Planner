import os
import random
import string
from bson import ObjectId
from collections import namedtuple

class Plan(namedtuple('Plan', ['obj_id', 'link', 'items', 'groups'])):
    """Wrapper to override constructor so that this named tuple 
    can be given default arguments."""

    def __new__(cls, link, obj_id=None, items=[], groups={}):
        return super(Plan, cls).__new__(cls, obj_id, link, items, groups)

class PlansRepo(object):

    def __init__(self, app, conn):
        self.app = app
        self.conn = conn

    #TODO: Move
    def generate_link(self, l=10):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(l))

    #TODO: Rename
    #TODO: Can this method be simplified/split up?
    #TODO: Use some of the other repositories?
    def get_plan_from_link(self, link): 
        self.app.logger.info("Reading link from database")
        link_data = self.conn.db.links.find_one({"link":link})
        if not link_data:
            return None
        self.app.logger.info("Link found - getting items and groups")
        link_id = link_data["_id"]
        pipeline = [
            {"$match": {"link": link_id}},
            {"$lookup":{"from":"groups", "localField":"group", "foreignField":"_id", "as":"group"}},
            {"$project":{"_id":1, "checked":1, "name":1, "group":{"$let":{"vars":{"field":{"$arrayElemAt":["$group",0]}},"in": "$$field.name"}}}},
        ]
        result = self.conn.db.items.aggregate(pipeline)
        if not result:
            self.app.logger.info("Empty data - returning plan")
            return Plan(
                        link=link,
                        items=[],
                        groups= {}
                    )
        self.app.logger.info("Building items + groups into plan")
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

    def __init__(self, app, conn):
        self.app = app
        self.conn = conn

    def generate_link_text(self, l=10):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(l))

    def create_link(self):
        self.app.logger.info('Attempting to create a link')
        new_link_text = self.generate_link_text()
        self.app.logger.info('Link text generated ' + new_link_text)
        inserted_id = self.conn.db.links.insert_one({"link": new_link_text}).inserted_id
        self.app.logger.info('Link inserted with id ' + str(inserted_id))
        return {"_id": str(inserted_id), "link": new_link_text}

    def get_obj_id_link(self, link):
        return str(self.conn.db.links.find_one({"link":link})["_id"])


class ItemRepo(object):

    def __init__(self, app, conn):
        self.app = app
        self.conn = conn

    def create_item(self, name, link_id, checked=False, group_id=""):
        self.app.logger.info('Attempting to create item with name ' + name)
        self.app.logger.info('Link for item creation is ' + link_id)
        link_obj_id = ObjectId(link_id)
        if group_id:
            group_obj_id = ObjectId(group_id)
        else:
            group_obj_id = ""
        item_data_to_insert = {'name': name,'checked': checked,'link': link_obj_id,'group': group_obj_id}
        inserted_id = self.conn.db.items.insert_one(item_data_to_insert).inserted_id
        item_data_to_insert["_id"] = str(inserted_id)
        item_data_to_insert["link"] = link_id
        self.app.logger.info('Item was created ' + str(item_data_to_insert))
        return item_data_to_insert

    def update_item(self, item_id, link_id, data):
        self.app.logger.info('Attempting to update item ' + item_id + " with data " + str(data))
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
        self.app.logger.info('Starting delete for item with ObjectId: ' + item_id)
        return self.conn.db.items.delete_one({"_id": ObjectId(item_id)}).deleted_count

    def get_items_by_group_id(self, group_id):
        self.app.logger.info('Getting items for group: ' + group_id)
        items = self.conn.db.items.find({"group": ObjectId(group_id)})
        return list(map(lambda i: str(i["_id"]), items))


class GroupRepo(object):

    def __init__(self, app, conn):
        self.app = app
        self.conn = conn

    def create_group(self, name, link_id):
        self.app.logger.info('Attempting to create group with name ' + name)
        self.app.logger.info('Link for group creation is ' + link_id)
        group_data_to_insert = {'name': name, 'link': ObjectId(link_id)}
        inserted_id = self.conn.db.groups.insert_one(group_data_to_insert).inserted_id
        group_data_to_insert["_id"] = str(inserted_id)
        group_data_to_insert["link"] = link_id

        self.app.logger.info('Group was created ' + str(group_data_to_insert))
        return group_data_to_insert

    def delete_group(self, group_id, item_repo):
        self.app.logger.info('Attempting to delete group ' + group_id)

        group_item_ids = item_repo.get_items_by_group_id(group_id)

        group_obj_id = ObjectId(group_id)

        #Note: What if this fails?
        group_deleted_count = self.conn.db.groups.delete_one({"_id": group_obj_id}).deleted_count
        self.app.logger.info('Number of groups deleted: ' + str(group_deleted_count))

        self.app.logger.info('Attempting to delete items from group ' + group_id)
        for item_id in group_item_ids:
            #Note: What if this fails?...
            item_repo.delete_item(item_id)
        
        self.app.logger.info('Deletion for group ' + group_id + " is complete")

        return 1

