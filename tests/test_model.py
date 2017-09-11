import unittest
from unittest.mock import MagicMock
from tests.utils import insert_link, insert_item, insert_group,get_all, drop_collection, get_all_groups, get_all_items
from app import app, PlansRepo, Plan, mongo, ItemRepo, GroupRepo, LinkRepo
from bson import ObjectId


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
        self.assertEqual(len(res.groups["groupA"]["items"]),0)
        self.assertEqual(len(res.groups["groupB"]["items"]),1)
        self.assertEquals(res.link, "abcdef")

    def tearDown(self):
        drop_collection()


class TestItemsGet(unittest.TestCase):

    def setUp(self):
       self.i_repo = ItemRepo(mongo)

    def test_get_items_empty_group(self):
        test_group_id = "A" * 24
        res = self.i_repo.get_items_by_group_id(test_group_id)
        self.assertEqual(res, [])

    def test_get_items_one_item_group(self):
        #TODO: Move id generator to a utility function
        test_group_id = "A" * 24 #should have length 24
        test_link_id = "B" * 24 #should have length 24
        inserted_item_id = self.i_repo.create_item("test", ObjectId(test_link_id), group_id=ObjectId(test_group_id))["_id"]
        res = self.i_repo.get_items_by_group_id(test_group_id)
        self.assertTrue(inserted_item_id in res)

    def test_get_items_three_items_group(self):
        test_group_id = "A" * 24 #should have length 24
        test_link_id = "B" * 24 #should have length 24
        inserted_item_ids = []
        inserted_item_ids.append(self.i_repo.create_item("test", ObjectId(test_link_id), group_id=ObjectId(test_group_id))["_id"])
        inserted_item_ids.append(self.i_repo.create_item("test2", ObjectId(test_link_id), group_id=ObjectId(test_group_id))["_id"])
        inserted_item_ids.append(self.i_repo.create_item("test3", ObjectId(test_link_id), group_id=ObjectId(test_group_id))["_id"])
        res = self.i_repo.get_items_by_group_id(test_group_id)
        for item_id in inserted_item_ids:
            self.assertTrue(item_id in res)

    def tearDown(self):
        drop_collection()

class TestGroupDelete(unittest.TestCase):

    def setUp(self):
        self.g_repo = GroupRepo(mongo)
        self.i_repo = ItemRepo(mongo)
        self.l_repo = LinkRepo(mongo)

    def test_delete_empty_group(self):
        test_link_id = self.l_repo.create_link()["_id"]
        test_group = "My Group"
        test_group_id = self.g_repo.create_group(name=test_group, link_id=ObjectId(test_link_id))["_id"]
        self.assertEquals(len(get_all_groups()), 1)

        self.g_repo.delete_group(test_group_id, self.i_repo)

        self.assertEquals(len(get_all_groups()), 0)

    def test_delete_group_with_items(self):
        test_link_id = self.l_repo.create_link()["_id"]
        test_group = "My Group"
        test_group_id = self.g_repo.create_group(name=test_group, link_id=ObjectId(test_link_id))["_id"]

        self.i_repo.create_item("test", ObjectId(test_link_id), group_id=ObjectId(test_group_id))
        self.i_repo.create_item("test2", ObjectId(test_link_id), group_id=ObjectId(test_group_id))
        self.i_repo.create_item("test3", ObjectId(test_link_id), group_id=ObjectId(test_group_id))

        self.assertEquals(len(get_all_items()), 3)
        self.assertEquals(len(get_all_groups()), 1)

        self.g_repo.delete_group(test_group_id, self.i_repo)

        self.assertEquals(len(get_all_groups()), 0)
        self.assertEquals(len(get_all_items()), 0)

    def tearDown(self):
        drop_collection()

