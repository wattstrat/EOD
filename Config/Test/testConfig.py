import unittest
import Config.config as config


class ConfigCommonTest(unittest.TestCase):

    '''
    python -m unittest Data.Cache.Test.TestDataCache from command line
    to launch test
    http://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure
    for more details
    '''

    def setUp(self):
        config.datacache.set_val('a', 2)
        config.datacache.set_val('c', 2)
        config.datacache.set_val('d', [1, 2, 3])

    def tearDown(self):
        config.datacache.del_val('a')
        config.datacache.del_val('c')
        config.datacache.del_val('d')

    def test_set_frommodule(self):
        self.assertEqual(
            config.datacache.__dict__['_cache_dict']['a']['value'], 2)

    def test_set(self):
        self.assertEqual(config.datacache.__dict__['_cache_dict']['c']['value'], 2)

    def test_set_list(self):
        self.assertEqual(
            config.datacache.__dict__['_cache_dict']['d']['value'], [1, 2, 3])

    def test_get_from_set(self):
        self.assertEqual(config.datacache.get_val('c'), 2)

    def test_get_from_setlist(self):
        self.assertEqual(config.datacache.get_val('d'), [1, 2, 3])

    def test_get_missing_variable(self):
        with self.assertRaises(KeyError) as raises:
            config.datacache.get_val('b')
            self.assertEqual(raises.exception.message, "b is not a valid key")

    def test_get_empty(self):
        self.assertEqual(config.datacache.get_val(), None)
