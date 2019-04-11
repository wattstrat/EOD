import unittest
import numpy as np
import pickle
from Data.DB.Mongo.mongo import Mongo


class DataMongoTest(unittest.TestCase):

    def setUp(self):
        print('\n [NEW TEST] -- %s \n' % self._testMethodName)
        self.x = Mongo(database="testalex", collection="colltestalex")
        self.x.set_val('a', 2, timestamp=0)

    def tearDown(self):
        self.x._client.drop_database("testalex")

    def test_set_val(self):
        cursor = self.x._collection.find_one()
        cursor["value"] = pickle.loads(cursor["value"])
        expected_dbdict = {"_metadata": {"timestamp_write": 0, "nbAccess":
                                         1, "poids": 0, "timestamp_read": 0}, "value": 2, "variable": "a"}
        expected_metadict = {
            "timestamp_write": 0, "nbAccess": 1, "poids": 0, "timestamp_read": 0}
        self.assertEqual(self.x._metadata['a'], expected_metadict)
        ooid = cursor.pop("_id")
        self.assertEqual(cursor, expected_dbdict)
        self.assertEqual(ooid, self.x._ooiddict['a'])
        self.x.set_val('a', 3, timestamp=1)
        cursor = self.x._collection.find_one()
        cursor["value"] = pickle.loads(cursor["value"])
        expected_dbdict = {"_metadata": {"timestamp_write": 1, "nbAccess":
                                         2, "poids": 0, "timestamp_read": 1}, "value": 3, "variable": "a"}
        expected_metadict = {
            "timestamp_write": 1, "nbAccess": 2, "poids": 0, "timestamp_read": 1}
        self.assertEqual(self.x._metadata['a'], expected_metadict)
        del cursor["_id"]
        self.assertEqual(cursor, expected_dbdict)
        self.assertEqual(ooid, self.x._ooiddict['a'])

    def test_get_val(self):
        expected_metadict = {
            "timestamp_write": 0, "nbAccess": 1, "poids": 0, "timestamp_read": 0}
        self.assertEqual(self.x._metadata['a'], expected_metadict)
        self.assertEqual(self.x.get_val('a', timestamp=1), 2)
        expected_metadict = {
            "timestamp_write": 0, "nbAccess": 2, "poids": 0, "timestamp_read": 1}
        self.assertEqual(self.x._metadata['a'], expected_metadict)

    def test_set_val_big(self):
        b = np.random.rand(2000, 2000)
        self.x.set_val('test', b)
        idx_rdm = np.random.randint(0, 2000)
        idy_rdm = np.random.randint(0, 2000)
        np.testing.assert_allclose(self.x.get_val('test'), b, rtol=1e-5, atol=0)


# test for logger in first set but nothing in second
