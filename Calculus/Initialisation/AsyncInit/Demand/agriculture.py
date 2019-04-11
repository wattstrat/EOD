import numpy as np

import Config.config as config
import babel.dot.initial_values as defcomp

from Utils.Numpy import div0
from Calculus.Initialisation.AsyncInit.asyncinit_entrypoint import Initialiser
from copy import deepcopy

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Agriculture(Initialiser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _compute(self, *args, **kwargs):
        surfini = np.array(self._cache.get_val('agri_surf_abs')) - config.NONZERO_VAL
        animalsini = np.array(self._cache.get_val('agri_animals_abs')) - config.NONZERO_VAL
        workersini = self._cache.get_val('agri_workers')
        firmsini = self._cache.get_val('agri_firms')
        populations = self._cache.get_val('population')
        varani = "Demand_Agriculture_Animals_Number_All_agrianimals_animalsnumber"
        varsurf = "Demand_Agriculture_Plants_Surface_All_agriplants_plantsurf"
        animax = max(animalsini)
        surfmax = max(surfini)
        for geocode in self.geocodes:
            geoidx = self.geo_indexes[geocode]
            tempdict = {'min': 0,
                        'max': 3 * animax,
                        'default': animalsini[geoidx],
                        'unit': 'Unité de gros bétail',
                        'operation_type': ('sum', 3),
                        'type': 'abs_val',
                        'unit_label': 'Cheptel, unité de gros bétail',
                        'metadata': {'Population du territoire': (int(populations[geoidx]), 'sum'),
                                     'Travail dans les exploitations agricoles (2010 - en unité de travail annuel)': (workersini[geoidx], 'sum'),
                                     'Exploitations agricoles (2010 - ayant leur siège dqns le territoire)': (firmsini[geoidx], 'sum')}
                        }
            self.geocodes[geocode][varani] = tempdict
            tempdict = {'min': 0,
                        'max': 3 * surfmax,
                        'default': surfini[geoidx],
                        'unit': 'Hectare',
                        'operation_type': ('sum', 3),
                        'type': 'abs_val',
                        'unit_label': 'Superficie agricole, ha',
                        'metadata': {'Population du territoire': (int(populations[geoidx]), 'sum'),
                                     'Travail dans les exploitations agricoles (2010 - en unité de travail annuel)': (workersini[geoidx], 'sum'),
                                     'Exploitations agricoles (2010 - ayant leur siège dqns le territoire)': (firmsini[geoidx], 'sum')}
                        }
            self.geocodes[geocode][varsurf] = tempdict
        return self.geocodes
