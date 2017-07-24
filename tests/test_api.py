import unittest
from flask import json
from tests.utils import drop_collection
from app import app, PlansRepo, Plan

class TestPlannerApiDataGet(unittest.TestCase):

    def test_get_planner_no_data(self):
        PlansRepo.insert(Plan(link="lkkkw", items=["a","b","c"]))
        with app.test_client() as c:
            rv = c.get('/api/planner/lkkkw')
            data = json.loads(rv.data)
            self.assertEqual(data['link'], "lkkkw")
            self.assertEqual(data['items'], ["a","b","c"])

    def tearDown(self):
        drop_collection()

