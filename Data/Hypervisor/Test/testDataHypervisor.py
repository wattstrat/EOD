import unittest


from Data.Hypervisor.hypervisor import Hypervisor

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DataHypervisorTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_stub(self):
        x = Hypervisor(
            metadata={'a': {"poids": 10, "timestamp_read": 1, "timestamp_write": 1, "nbAccess": 1}})
        nb = 5
        pX = 0
        for k in range(2, 100):
            with self.assertLogs(x.logger, level='DEBUG') as cm:
                x.get_val('a')
                nb = x.get_nb_access('a')
                pX = x.get_poids('a')
                x.logger.debug("NOLOGS")
            self.assertEqual(
                cm.output, ['DEBUG:Data.Hypervisor.hypervisor.Hypervisor:NOLOGS'])
            self.assertEqual(nb, k)
            self.assertEqual(pX, 10)
