from app import mongo

def insert_link(link, items, groups):
    return mongo.db.plans.insert({"link": link, "items": items, "groups": groups}) 
    
def get_all():
    return mongo.db.plans.find()
    
def drop_collection():
    mongo.db.plans.drop()
