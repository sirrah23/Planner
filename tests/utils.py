from app import mongo

def insert_link(link_name):
	return mongo.db.links.insert_one({'link':link_name}).inserted_id

def insert_item(name, link_id, checked=False, group_id=""):
	return mongo.db.items.insert_one({'name': name,'checked': checked,'link': link_id,'group': group_id,}).inserted_id

def insert_group(name, link_id):
	return mongo.db.groups.insert_one({'name': name,'link': link_id,}).inserted_id
    
def get_all():
    return mongo.db.plans.find()
    
def drop_collection():
    mongo.db.links.drop()
    mongo.db.items.drop()
    mongo.db.groups.drop()
    mongo.db.plans.drop()
