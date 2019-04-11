import unittest
import time
import random


from Data.data import Data

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DataTestGet(unittest.TestCase):

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

    def test_get_poidsDefault(self):
        x = Data()
        pX = 5
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            x.set_val('a', 2)
            pX = x.get_poids('a')
        self.assertEqual(
            cm.output, [
                'DEBUG:Data.data.Data: Data.get_poids: Missing metadata : '
                'varName = a',
                'DEBUG:Data.data.Data: Data.get_nb_access: Missing metadata : '
                'varName = a'])
        self.assertEqual(pX, 0)

    def test_get_nb_accessDefault(self):
        x = Data()

        with self.assertLogs(x.logger, level='DEBUG') as cm:
            x.set_val('a', 2)
            nb = x.get_nb_access('a')
        self.assertEqual(
            cm.output, [
                'DEBUG:Data.data.Data: Data.get_poids: Missing metadata : '
                'varName = a',
                'DEBUG:Data.data.Data: Data.get_nb_access: Missing metadata : '
                'varName = a'])
        self.assertEqual(nb, 1)

    def test_get_poids(self):
        x = Data()
        x.set_val('a', 2, poids=1000)
        pX = 5
        for k in [random.randint(0, 100) for j in range(1, 100)]:
            with self.assertLogs(x.logger, level='DEBUG') as cm:
                x.set_val('a', 2, poids=k)
                pX = x.get_poids('a')
                x.logger.debug("NOLOGS")
            self.assertEqual(cm.output, ['DEBUG:Data.data.Data:NOLOGS'])
            self.assertEqual(pX, k)

    def test_get_nb_access(self):
        x = Data()
        x.set_val('a', 2)
        nb = 5
        for k in range(2, 100):
            with self.assertLogs(x.logger, level='DEBUG') as cm:
                x.get_val('a')
                nb = x.get_nb_access('a')
                x.logger.debug("NOLOGS")
            self.assertEqual(cm.output, ['DEBUG:Data.data.Data:NOLOGS'])
            self.assertEqual(nb, k)

    def test_get_poidsMissing(self):
        x = Data()
        pX = 5
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            pX = x.get_poids('a')
        self.assertEqual(
            cm.output, ['WARNING:Data.data.Data: Data.get_poids: '
                        'Missing metadata : varName = a'])
        self.assertEqual(pX, 0)

    def test_get_nb_accessMissing(self):
        x = Data()
        with self.assertLogs(x.logger, level='DEBUG') as cm:
            nb = x.get_nb_access('a')
        self.assertEqual(
            cm.output, ['WARNING:Data.data.Data: Data.get_nb_access: '
                        'Missing metadata : varName = a'])
        self.assertEqual(nb, 0)

    def test_get_poidsMissingLogFun(self):
        x = Data()
        pX = 5
        with self.assertLogs(x.logger, level='ERROR') as cm:
            pX = x.get_poids('a', logFun=x.logger.error)
        self.assertEqual(
            cm.output, ['ERROR:Data.data.Data: Data.get_poids: '
                        'Missing metadata : varName = a'])
        self.assertEqual(pX, 0)

    def test_get_nb_accessMissingLogFun(self):
        x = Data()
        with self.assertLogs(x.logger, level='ERROR') as cm:
            nb = x.get_nb_access('a', logFun=x.logger.error)
        self.assertEqual(
            cm.output, ['ERROR:Data.data.Data: Data.get_nb_access: '
                        'Missing metadata : varName = a'])
        self.assertEqual(nb, 0)

    def test_getMissingPoids(self):
        x = Data(metadata={'a': {}})
        pX = 5
        with self.assertLogs(x.logger, level='ERROR') as cm:
            pX = x.get_poids('a')
        self.assertEqual(
            cm.output, ['ERROR:Data.data.Data: Data.get_poids: '
                        'Missing poids metadata : varName = a'])
        self.assertEqual(pX, 0)

    def test_getMissingNbAccess(self):
        x = Data(metadata={'a': {}})
        with self.assertLogs(x.logger, level='ERROR') as cm:
            nb = x.get_nb_access('a')
        self.assertEqual(
            cm.output, ['ERROR:Data.data.Data: Data.get_nb_access: '
                        'Missing nbAccess metadata : varName = a'])
        self.assertEqual(nb, 0)
