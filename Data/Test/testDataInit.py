import unittest
import time
import random
from Data.data import Data


class DataTestInit(unittest.TestCase):

    '''
    python -m unittest Data.Cache.Test.TestDataCache from command line
    to launch test
    http://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure
    for more details
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # Testing Initialisation

    def test_initialiseMetadata(self):
        x = Data(
            metadata={'a': {"poids": 0,
                            "timestamp_read": 1,
                            "timestamp_write": 1,
                            "nbAccess": 10}})
        self.assertEqual(x.__dict__['_metadata'], {
                         'a': {"poids": 0,
                               "timestamp_read": 1,
                               "timestamp_write": 1,
                               "nbAccess": 10}})
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            x.set_val('b', 2, timestamp=100)
        self.assertEqual(
            cm.output, [
                'DEBUG:Data.data.Data: Data.get_poids: Missing metadata : '
                'varName = b',
                'DEBUG:Data.data.Data: Data.get_nb_access: Missing metadata : '
                'varName = b'])
        self.assertEqual(
            x.__dict__['_metadata'], {'a':
                                      {"poids": 0,
                                       "timestamp_read": 1,
                                       "timestamp_write": 1,
                                       "nbAccess": 10},
                                      'b':
                                      {"poids": 0,
                                       "timestamp_read": 100,
                                       "timestamp_write": 100,
                                       "nbAccess": 1}})

    def test_initialiseMetadataMissingPoids(self):
        x = Data(
            metadata={'a': {"timestamp_read": 1,
                            "timestamp_write": 1,
                            "nbAccess": 10}})
        with self.assertLogs(x.logger, level='ERROR') as cm:
            x.set_val('a', 2, timestamp=100)
        self.assertEqual(
            cm.output, ['ERROR:Data.data.Data: Data.get_poids: '
                        'Missing poids metadata : varName = a'])
        self.assertEqual(x.__dict__['_metadata'], {'a':
                                                   {"poids": 0,
                                                    "timestamp_read": 100,
                                                    "timestamp_write": 100,
                                                    "nbAccess": 11}})

    def test_initialiseMetadataMissingNbAccess(self):
        x = Data(
            metadata={'a': {"timestamp_read": 1,
                            "timestamp_write": 1,
                            "poids": 10}})
        with self.assertLogs(x.logger, level='ERROR') as cm:
            x.set_val('a', 2, timestamp=100)
        self.assertEqual(
            cm.output, ['ERROR:Data.data.Data: Data.get_nb_access: '
                        'Missing nbAccess metadata : varName = a'])
        self.assertEqual(x.__dict__['_metadata'], {'a':
                                                   {"poids": 10,
                                                    "timestamp_read": 100,
                                                    "timestamp_write": 100,
                                                    "nbAccess": 1}})
