

from Data.Hypervisor.Politics.RamDBPolitic import RamDBPolitic, RamDBPoliticWithDefaultCleanup
from Data.Hypervisor.Politics.DataCalculusPolitic import DataCalculusPolitic

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class RamDBCalculusPolitic(DataCalculusPolitic):
    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        super().__init__(RamDBPolitic(*args, **kwargs), *args, **kwargs)


class RamDBCalculusPoliticWithDefaultCleanup(DataCalculusPolitic):
    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        cache = RamDBPoliticWithDefaultCleanup(*args, **kwargs)
        super().__init__(cache, *args, **kwargs)


# TODO
class SizedRamDBCalculusPoliticWithDefaultCleanup(RamDBCalculusPoliticWithDefaultCleanup):
    pass
