import unittest
from Data.Hypervisor.Politics.RamDBPolitic import RamDBPolitic


class RamDBPoliticTest(unittest.TestCase):

    def setUp(self):
        kwargs = {"DB-opt": {"database": "testalex", "collection": "colltestalex"}}
        self.x = RamDBPolitic(**kwargs)
        self.x.set_val('a', 2, timestamp=1234)
        self.x._RamDBPolitic__cache_db.set_val('b', 3, timestamp=90)

    def tearDown(self):
        self.x._RamDBPolitic__cache_db._client.drop_database("testalex")

    def test_set_val_RAM(self):
        self.assertEqual(self.x._RamDBPolitic__cache_ram._cache_dict, {
                         'a': {'timestamp_read': 1234, 'value': 2, 'timestamp_write': 1234}})

    def test_metadata_set_RAM(self):
        self.assertEqual(self.x._RamDBPolitic__cache_ram._metadata, {
                         'a': {'timestamp_read': 1234, 'nbAccess': 1, 'timestamp_write': 1234, 'poids': 0}})

    def test_get_val_RAM(self):
        self.assertEqual(self.x.get_val('a', timestamp=1239), 2)
        self.assertEqual(self.x._RamDBPolitic__cache_ram._metadata, {
                         'a': {'timestamp_read': 1239, 'nbAccess': 2, 'timestamp_write': 1234, 'poids': 0}})

    def test_get_nonexisting_RAM(self):
        with self.assertLogs(self.x.logger, level='DEBUG') as cm:
            temp = self.x.get_val('b')
        self.assertEqual(temp, 3)
        self.assertEqual(cm.output, [
            'DEBUG:Data.Hypervisor.Politics.RamDBPolitic.RamDBPolitic:No variable named b in the RAM, checking in db'])
