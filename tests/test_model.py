import unittest
from app import app, PlansRepo, mongo, Plan

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

class TestPlansInsert(unittest.TestCase):

    def test_insert_empty_link(self):
        p_to_insert = Plan(link="qwerty")
        inserted_id = PlansRepo.insert(p_to_insert)
        p_inserted = PlansRepo.get_plan_from_link("qwerty")
        self.assertEqual(get_all().count(), 1)
        self.assertEqual(inserted_id, p_inserted.obj_id)
        self.assertEqual(p_inserted.link, "qwerty")
        self.assertEqual(p_inserted.items, [])
        self.assertEqual(p_inserted.groups, {})

    def test_insert_link_items(self):
        p_to_insert = Plan(link="qwerty", items=["a", "b", "c"])
        inserted_id = PlansRepo.insert(p_to_insert)
        p_inserted = PlansRepo.get_plan_from_link("qwerty")
        self.assertEqual(get_all().count(), 1)
        self.assertEqual(inserted_id, p_inserted.obj_id)
        self.assertEqual(p_inserted.link, "qwerty")
        self.assertEqual(p_inserted.items, ["a", "b", "c"])
        self.assertEqual(p_inserted.groups, {})

    def tearDown(self):
        drop_collection()
