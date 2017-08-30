import unittest
from flask import json
from bson import ObjectId
from tests.utils import drop_collection
from app import app, LinkRepo, ItemRepo, mongo

class TestPlannerApiDataGet(unittest.TestCase):

    def setUp(self):
        self.l_repo = LinkRepo(mongo)
        self.i_repo = ItemRepo(mongo)

    def test_get_planner_no_data(self):
        new_link = self.l_repo.create_link()
        self.i_repo.create_item('a', ObjectId(new_link['_id']))
        self.i_repo.create_item('b', ObjectId(new_link['_id']))
        self.i_repo.create_item('c', ObjectId(new_link['_id']))
        with app.test_client() as c:
            rv = c.get('/api/v1/planner/' + new_link['link'])
            data = json.loads(rv.data)
            self.assertEqual(data['link'], new_link['link'])
            inserted_names = map(lambda i: i['name'], data['items'])
            for i in ['a', 'b', 'c']:
                self.assertEqual(i in inserted_names, True)
            for i in data['items']:
                self.assertEqual(i['checked'], False)

    def tearDown(self):
        drop_collection()

