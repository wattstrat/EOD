import unittest
import time
import random


from Data.data import Data
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DataTestSet(unittest.TestCase):

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

    # Testing Set

    def test_setPoidsDefault(self):
        x = Data()
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            x.set_val('a', 2)
        self.assertEqual(
            cm.output, [
                'DEBUG:Data.data.Data: Data.get_poids: Missing metadata : '
                'varName = a',
                'DEBUG:Data.data.Data: Data.get_nb_access: Missing metadata : '
                'varName = a'])
        self.assertEqual(x.__dict__['_metadata']['a']['poids'], 0)

    def test_setNbAccessDefault(self):
        x = Data()
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            x.set_val('a', 2)
        self.assertEqual(
            cm.output, [
                'DEBUG:Data.data.Data: Data.get_poids: Missing metadata : '
                'varName = a',
                'DEBUG:Data.data.Data: Data.get_nb_access: Missing metadata : '
                'varName = a'])
        self.assertEqual(x.__dict__['_metadata']['a']['nbAccess'], 1)

    def test_setTimestampsDefault(self):
        x = Data()
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            t1 = time.time()
            x.set_val('a', 2)
            t2 = time.time()
        self.assertEqual(
            cm.output, [
                'DEBUG:Data.data.Data: Data.get_poids: Missing metadata : '
                'varName = a',
                'DEBUG:Data.data.Data: Data.get_nb_access: Missing metadata : '
                'varName = a'])
        self.assertTrue(t1 <= x.__dict__['_metadata']['a']['timestamp_read'])
        self.assertTrue(x.__dict__['_metadata']['a']['timestamp_read'] <= t2)
        self.assertEqual(x.__dict__['_metadata']['a'][
            'timestamp_read'], x.__dict__['_metadata']['a']['timestamp_write'])

    def test_setPoids(self):
        x = Data()
        x.set_val('a', 2, poids=1000)
        for k in [random.randint(0, 100) for j in range(1, 100)]:
            with self.assertLogs(x.logger, level='DEBUG') as cm:
                x.set_val('a', 2, poids=k)
                x.logger.debug("NOLOGS")
            self.assertEqual(cm.output, ['DEBUG:Data.data.Data:NOLOGS'])
            self.assertEqual(x.__dict__['_metadata']['a']['poids'], k)

    def test_setPoidsChoice(self):
        x = Data()
        curPoids = 0
        x.set_val('a', 2, poids=curPoids)
        for k in [random.randint(0, 100) for j in range(1, 100)]:
            with self.assertLogs(x.logger, level='DEBUG') as cm:
                if random.choice([True, False]):
                    curPoids = k
                    x.set_val('a', 2, poids=k)
                else:
                    x.set_val('a', 2)
                x.logger.debug("NOLOGS")
            self.assertEqual(cm.output, ['DEBUG:Data.data.Data:NOLOGS'])
            self.assertEqual(x.__dict__['_metadata']['a']['poids'], curPoids)

    def test_setNbAccess(self):
        x = Data()
        x.set_val('a', 2)
        for k in range(2, 100):
            with self.assertLogs(x.logger, level='DEBUG') as cm:
                x.set_val('a', 2)
                x.logger.debug("NOLOGS")
            self.assertEqual(cm.output, ['DEBUG:Data.data.Data:NOLOGS'])
            self.assertEqual(x.__dict__['_metadata']['a']['nbAccess'], k)

    def test_setTimestamps(self):
        x = Data()
        x.set_val('a', 2)
        for k in [random.randint(0, 100) for j in range(1, 100)]:
            with self.assertLogs(x.logger, level='DEBUG') as cm:
                x.set_val('a', 2, timestamp=k)
                x.logger.debug("NOLOGS")
            self.assertEqual(cm.output, ['DEBUG:Data.data.Data:NOLOGS'])
            self.assertEqual(x.__dict__['_metadata']['a']['timestamp_read'], k)
            self.assertEqual(
                x.__dict__['_metadata']['a']['timestamp_write'], k)
