import unittest
from app import app, PlansRepo, mongo

# Testing utilities
def insert_link(link, items, groups):
    return mongo.db.plans.insert({"link": link, "items": items, "groups": groups}) 
    
def get_all():
    return mongo.db.plans.find()
    
def drop_collection():
    mongo.db.plans.drop()

class TestPlansGet(unittest.TestCase):

    def test_get_nonexistent_link(self):
        res = PlansRepo.get_plan_from_link("abcdef")
        self.assertEquals(res, None)

    def test_get_empty_link(self):
        insert_link("abcdef", [], {})
        res = PlansRepo.get_plan_from_link("abcdef")
        self.assertEquals(res.link, "abcdef")
        self.assertEquals(res.items, [])
        self.assertEquals(res.groups, {})

    def test_get_link_items_only(self):
        insert_link("abcdef", ["a", "b", "c"], {})
        res = PlansRepo.get_plan_from_link("abcdef")
        self.assertEquals(res.link, "abcdef")
        self.assertEquals(res.items, ["a", "b", "c"])
        self.assertEquals(res.groups, {})

    def test_get_link_items_and_groups(self):
        insert_link("abcdef", ["a", "b", "c"], {"groupA":[], "groupB": ["aa"]})
        res = PlansRepo.get_plan_from_link("abcdef")
        self.assertEquals(res.link, "abcdef")
        self.assertEquals(res.items, ["a", "b", "c"])
        self.assertEquals(res.groups, {"groupA":[], "groupB": ["aa"]})

    def tearDown(self):

        drop_collection()
