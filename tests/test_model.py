import unittest
from app import app, Plans, mongo

# Testing utilities
def insert_link(link, items, groups):
    return mongo.db.plans.insert({"link": link, "items": items, "groups": groups}) 
    
def get_all():
    return mongo.db.plans.find()
    
def drop_collection():
    mongo.db.plans.drop()

class TestPlansGet(unittest.TestCase):

    def test_get_nonexistent_link(self):
        res = Plans.get_plan_from_link("abcdef")
        self.assertEquals(res["status"], "fail")
        self.assertEquals(res["errormsg"], "Non-existent link")
        self.assertEquals(res["data"], {})

    def test_get_empty_link(self):
        insert_link("abcdef", [], {})
        res = Plans.get_plan_from_link("abcdef")
        self.assertEquals(res["status"], "success")
        self.assertEquals(res["errormsg"], "")
        self.assertEquals(res["data"]["link"], "abcdef")
        self.assertEquals(res["data"]["items"], [])
        self.assertEquals(res["data"]["groups"], {})

    def test_get_link_items_only(self):
        insert_link("abcdef", ["a", "b", "c"], {})
        res = Plans.get_plan_from_link("abcdef")
        self.assertEquals(res["status"], "success")
        self.assertEquals(res["errormsg"], "")
        self.assertEquals(res["data"]["link"], "abcdef")
        self.assertEquals(res["data"]["items"], ["a", "b", "c"])
        self.assertEquals(res["data"]["groups"], {})

    def test_get_link_items_and_groups(self):
        insert_link("abcdef", ["a", "b", "c"], {"groupA":[], "groupB": ["aa"]})
        res = Plans.get_plan_from_link("abcdef")
        self.assertEquals(res["status"], "success")
        self.assertEquals(res["errormsg"], "")
        self.assertEquals(res["data"]["link"], "abcdef")
        self.assertEquals(res["data"]["items"], ["a", "b", "c"])
        self.assertEquals(res["data"]["groups"], {"groupA":[], "groupB": ["aa"]})

    def tearDown(self):
        drop_collection()
