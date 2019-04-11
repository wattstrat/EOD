import unittest
from Data.RAM.RAM import RAM
from Data.DB.Mongo.mongo import Mongo
from Data.Hypervisor.Politics.RamDBCalculusPolitic import RamDBCalculusPolitic
# TODO: en cours.


class RamDBPoliticGlobalTest(unittest.TestCase):

    '''
    python -m unittest Data.RAM.Test.TestDataRAM from command line to launch test
    http://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure
    for more details
    '''

    def setUp(self):
        kwargs = {'DB-opt': {'database': "RamDBPoliticGlobalTest", 'collection': "default"}}
        self._data = RamDBCalculusPolitic(**kwargs)

    def tearDown(self):
        temp = self._data._RamDBCalculusPolitic__cache_ramdb
        temp._RamDBPolitic__cache_db._client.drop_database("RamDBPoliticGlobalTest")

    def test_set(self):
        self._data.set_val('bob', 2)
        self.assertEqual(self._data.get_val('bob'), 2)

    def test_get_missing(self):
        with self.assertRaises(KeyError) as raises:
            self._data.get_val('dod')
            self.assertEqual(raises.exception.message, "dod is not a valid key")
