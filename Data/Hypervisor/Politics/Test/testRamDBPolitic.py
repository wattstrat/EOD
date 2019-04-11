import unittest
from Data.RAM.RAM import RAM
from Data.DB.Mongo.mongo import Mongo
from Data.Hypervisor.Politics.RamDBPolitic import RamDBPolitic
# TODO: en cours.


class RamDBPoliticCommonTest(unittest.TestCase):

    '''
    python -m unittest Data.RAM.Test.TestDataRAM from command line to launch test
    http://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure
    for more details
    '''

    def setUp(self):
        kwargs = {'DB-opt': {'database': "RamDBPoliticCommonTest", 'collection': "default"}}
        self._data = RamDBPolitic(**kwargs)

    def tearDown(self):
        self._data._RamDBPolitic__cache_db._client.drop_database("RamDBPoliticCommonTest")

    def test_set(self):
        x = RAM()
        x.set_val('a', 2)
        self.assertEqual(x.__dict__['_cache_dict']['a']['value'], 2)

    def test_set_list(self):
        x = RAM()
        x.set_val('a', [1, 2, 3])
        # verifier que le dict = {a:{value etc}} pour etre sur que rien d'autre
        # n'est la
        self.assertEqual(x.__dict__['_cache_dict']['a']['value'], [1, 2, 3])

    def test_get_from_set(self):
        x = RAM()
        x.set_val('a', 2)
        self.assertEqual(x.get_val('a'), 2)

    def test_get_from_setlist(self):
        x = RAM()
        x.set_val('a', [1, 2, 3])
        self.assertEqual(x.get_val('a'), [1, 2, 3])

    def test_get_from_scratch(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.get_val('a'), 2)

    def test_get_missing_variable(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        with self.assertRaises(KeyError) as raises:
            x.get_val('b')
            self.assertEqual(raises.exception.message, "b is not a valid key")

    def test_get_empty(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.get_val(None), None)

    def test_getWritestamp(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.get_writestamp('a'), 12)

    def test_getReadstamp(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.get_readstamp('a'), 34)

    def test_RamDB_get_missing(self):
        with self.assertRaises(KeyError) as raises:
            self._data.get_val('dod')
            self.assertEqual(raises.exception.message, "dod is not a valid key")
