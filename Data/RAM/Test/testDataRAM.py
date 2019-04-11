import unittest
from Data.RAM.RAM import RAM
import numpy as np


class DataRAMCommonTest(unittest.TestCase):

    '''
    python -m unittest Data.RAM.Test.TestDataRAM from command line to launch test
    http://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure
    for more details
    '''

    def setUp(self):
        pass

    def tearDown(self):
        pass

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

    def test_set_val_big(self):
        b = np.random.rand(2000, 2000)
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        x.set_val('b', b)
        idx_rdm = np.random.randint(0, 2000)
        idy_rdm = np.random.randint(0, 2000)
        np.testing.assert_allclose(x.get_val('b'), b, rtol=1e-5, atol=0)
