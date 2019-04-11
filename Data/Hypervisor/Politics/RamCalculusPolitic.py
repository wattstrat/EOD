

from Data.RAM.RAM import RAM
from Data.Hypervisor.Politics.DataCalculusPolitic import DataCalculusPolitic

import Config.variables as variables
import Config.config as config


if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class RamCalculusPolitic(DataCalculusPolitic):
    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        super().__init__(RAM(*args, **kwargs), *args, **kwargs)
