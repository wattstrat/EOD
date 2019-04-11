
import re
from toposort import toposort

from Calculus.Constants.Constants import Constants

import Config.config as config
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class SectorsDependancesOrder(Constants):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._poids = 100

    def _run(self):
        return [[(sector, list(toposort(config.varnames_dependances[sector])))
                 for sector in sectors_set]
                for sectors_set in toposort(config.sectors_dependances)]


# Group sectors in MetaSectors => no more inter-dependance
class MetaSectors(Constants):
    # Fastest without order preserving
    # From: http://code.activestate.com/recipes/52560/

    @staticmethod
    def uniq(alist):
        return list(set(alist))

    @staticmethod
    def uniq_sort(alist):
        return sorted(set(alist))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._poids = 100

    def _run(self):
        default_matrix_hypothesis_order = self._cache.get_val('Hypothesis:Default:Order')
        consumption = [re.compile('_Consumption'),
                       re.compile('_Dispatchable'),
                       re.compile('_Fatal')]
        if __debug__:
            logger.debug('%s', default_matrix_hypothesis_order.keys())
        first_match = [conso.sub('', key_param) for conso in consumption
                       for key_param in default_matrix_hypothesis_order.keys()
                       if conso.search(key_param) is not None]
        simultaneous_filtered = []
        for sector in first_match:
            if sector in config.simultaneous_sectors:
                simultaneous_filtered.append(config.simultaneous_sectors[sector])
            else:
                simultaneous_filtered.append(sector)
        added_non_config_sectors = config.non_config_sectors + self.uniq_sort(simultaneous_filtered)
        return [added_non_config_sectors]
