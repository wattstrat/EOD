import unittest
import time
import random


from Data.data import Data
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DataTestDel(unittest.TestCase):

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

    # Testing Del

    def test_del_valMissing(self):
        x = Data()
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            x.del_val('a')
        self.assertEqual(
            cm.output, ['ERROR:Data.data.Data: KeyError in del_val : '
                        'varName = a'])

    def test_del_val(self):
        x = Data()
        x.set_val('a', 2)
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            x.del_val('a')
            x.logger.debug("NOLOGS")
        self.assertEqual(cm.output, ['DEBUG:Data.data.Data:NOLOGS'])
        self.assertNotIn('a', x.__dict__['_metadata'])
