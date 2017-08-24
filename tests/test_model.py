import unittest
from unittest.mock import MagicMock
from tests.utils import insert_link, insert_item, insert_group,get_all, drop_collection
from app import app, PlansRepo, Plan, mongo

    
class TestPlansGet(unittest.TestCase):

    def setUp(self):
       self.p_repo = PlansRepo(mongo)

    def test_get_nonexistent_link(self):
        res=self.p_repo.get_plan_from_link("abcdef")
        self.assertEquals(res, None)

    def test_get_empty_link(self):
        insert_link("abcdef")
        res =self.p_repo.get_plan_from_link("abcdef")
        self.assertEquals(res.link, "abcdef")
        self.assertEquals(res.items, [])
        self.assertEquals(res.groups, {})

    def test_get_link_items_only(self):
        link_id = insert_link("abcdef")
        insert_item("a", link_id)
        insert_item("b", link_id)
        insert_item("c", link_id)
        res =self.p_repo.get_plan_from_link("abcdef")
        self.assertEquals(res.link, "abcdef")
        item_names = map(lambda i: i['name'], res.items)
        for i in ["a", "b", "c"]:
            self.assertEquals(i in item_names,True)
        self.assertEquals(res.groups, {})

    def test_get_link_items_and_groups(self):
        link_id=insert_link("abcdef")
        insert_group("groupA", link_id)
        group_id = insert_group("groupB", link_id)
        insert_item("a", link_id)
        insert_item("b", link_id)
        insert_item("c", link_id)
        insert_item("aa", link_id, group_id=group_id)
        res =self.p_repo.get_plan_from_link("abcdef")
        item_names = map(lambda i: i['name'], res.items)
        for i in ["a", "b", "c"]:
            self.assertEquals(i in item_names,True)
        self.assertEqual("groupA" in res.groups.keys(),True)
        self.assertEqual("groupB" in res.groups.keys(),True)
        self.assertEqual(len(res.groups["groupA"]),0)
        self.assertEqual(len(res.groups["groupB"]),1)
        self.assertEquals(res.link, "abcdef")

    def tearDown(self):
        drop_collection()

class TestPlansInsert(unittest.TestCase):

    def setUp(self):
        self.p_repo = PlansRepo(mongo)

    def test_insert_empty_link(self):
        p_to_insert = Plan(link="qwerty")
        inserted_id =self.p_repo.insert(p_to_insert)
        p_inserted =self.p_repo.get_plan_from_link("qwerty")
        self.assertEqual(get_all().count(), 1)
        self.assertEqual(p_inserted.link, "qwerty")
        self.assertEqual(p_inserted.items, [])
        self.assertEqual(p_inserted.groups, {})

    def test_insert_link_items(self):
        p_to_insert = Plan(link="qwerty", items=["a", "b", "c"])
        inserted_id =self.p_repo.insert(p_to_insert)
        p_inserted =self.p_repo.get_plan_from_link("qwerty")
        self.assertEqual(get_all().count(), 1)
        self.assertEqual(p_inserted.link, "qwerty")
        self.assertEqual(p_inserted.items, ["a", "b", "c"])
        self.assertEqual(p_inserted.groups, {})

    def test_insert_empty_argument(self):
        inserted_id =self.p_repo.insert()
        p_inserted =self.p_repo.get_plan_from_link(inserted_id)
        self.assertEqual(get_all().count(), 1)
        self.assertEqual(p_inserted.items, [])
        self.assertEqual(p_inserted.groups, {})

    def tearDown(self):
        drop_collection()

class TestPlansUpdate(unittest.TestCase):

    def setUp(self):
        self.mongo_mock = MagicMock()
        self.p_repo = PlansRepo(self.mongo_mock)

    def test_update_existing_link(self):
        #TODO: Create an anonymous object utility wrapper around this thing...
        self.mongo_mock.db.plans.update_one.return_value = type('',(object,),{"modified_count":1})()
        res = self.p_repo.update("lkkkw", {"items":["a", "b"]})
        self.mongo_mock.db.plans.update_one\
                .assert_called_with({"link": "lkkkw"}, {"$set":{"items":["a", "b"]}})
        self.assertEqual(res, True)

    def test_update_nonexistent_link(self):
        #TODO: Create an anonymous object utility wrapper around this thing...
        self.mongo_mock.db.plans.update_one.return_value = type('',(object,),{"modified_count":0})()
        res = self.p_repo.update("lkkkw", {"items":["a", "b"]})
        self.mongo_mock.db.plans.update_one\
                .assert_called_with({"link": "lkkkw"}, {"$set":{"items":["a", "b"]}})
        self.assertEqual(res, False)
