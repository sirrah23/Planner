import unittest
from flask import json
from bson import ObjectId
from tests.utils import drop_collection
from app import app, mongo
from app.models import LinkRepo, ItemRepo

class TestPlannerApiDataGet(unittest.TestCase):

    def setUp(self):
        self.l_repo = LinkRepo(app, mongo)
        self.i_repo = ItemRepo(app, mongo)

    def test_get_planner_no_data(self):
        new_link = self.l_repo.create_link()
        self.i_repo.create_item('a', new_link['_id'])
        self.i_repo.create_item('b', new_link['_id'])
        self.i_repo.create_item('c', new_link['_id'])
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

