

from Data.Hypervisor.Politics.ListedDataPolitic import ListedDataPolitic, ListedDataPoliticWithDefaultCleanup
from Data.Hypervisor.Politics.DataCalculusPolitic import DataCalculusPolitic

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class ListedDataCalculusPolitic(DataCalculusPolitic):
    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        super().__init__(ListedDataPolitic(*args, **kwargs), *args, **kwargs)


class ListedDataCalculusPoliticWithDefaultCleanup(DataCalculusPolitic):
    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        cache = ListedDataPoliticWithDefaultCleanup(*args, **kwargs)
        super().__init__(cache, *args, **kwargs)
