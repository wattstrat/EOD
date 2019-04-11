import unittest
from Data.RAM.ram import RAM

# TODO: revoir tout!


class DataRAMCommonTest(unittest.TestCase):

    '''
    python -m unittest Data.RAM.Test.TestDataRAM from command line to launch test
    http://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure
    for more details
    '''

    def setUp(self):
        self._ram = SizedRAM(500)

    def tearDown(self):
        pass

    def test_init(self):
        self.assertEqual(self._ram.__dict__['_max_size'], 500)
        self.assertEqual(self._ram.__dict__['_size'], 0)
        self.assertEqual(self._ram.__dict__['_obj_size'], {})

    def test_size(self):
        x.setVal('a', 2)
        self.assertEqual(
            self._ram.__dict__['_max_size'], self._ram.__dict__['_obj_size']['a'])

    def test_set_list(self):
        x = RAM()
        x.setVal('a', [1, 2, 3])
        # verifier que le dict = {a:{value etc}} pour etre sur que rien d'autre
        # n'est la
        self.assertEqual(x.__dict__['_cache_dict']['a']['value'], [1, 2, 3])

    def test_get_from_set(self):
        x = RAM()
        x.setVal('a', 2)
        self.assertEqual(x.getVal('a'), 2)

    def test_get_from_setlist(self):
        x = RAM()
        x.setVal('a', [1, 2, 3])
        self.assertEqual(x.getVal('a'), [1, 2, 3])

    def test_get_from_scratch(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.getVal('a'), 2)

    def test_get_missing_variable(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        with self.assertRaises(KeyError) as raises:
            x.getVal('b')
            self.assertEqual(raises.exception.message, "b is not a valid key")

    def test_get_empty(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.getVal(), None)

    def test_getWritestamp(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.getWritestamp('a'), 12)

    def test_getReadstamp(self):
        x = RAM(
            initial={'a': {'value': 2, "timestamp_write": 12, "timestamp_read": 34}})
        self.assertEqual(x.getReadstamp('a'), 34)
