import numpy as np

import pymongo

import Config.variables as variables
import Config.config as config
import babel.dot.initial_values as defcomp
from Calculus.calculus import Calculus

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class WindDistribMask(Calculus):

    def _run(self, **kwargs):
        distrib_ini = self._cache.get_val('Supply:Wind:Turbines:Distribution:Ini', run_args=['Eolien_power_MW'])
        # distrib_frac = distrib_ini / sum(distrib_ini)
        return distrib_ini / 1e6


class PVDistribMask(Calculus):

    def _run(self, **kwargs):
        distrib_ini = self._cache.get_val('Supply:Solar:PV:Distribution:Ini',
                                          run_args=['Solaire photovoltaïque_power_MW'])
        # distrib_frac = distrib_ini / sum(distrib_ini)
        return distrib_ini / 1e6


class HydroRunDistribMask(Calculus):

    def _run(self, **kwargs):
        distrib_ini = self._cache.get_val('Supply:HydroRun:Distrib:Ini')
        # distrib_frac = distrib_ini / sum(distrib_ini)
        return distrib_ini / 1e6


class DispatchableDistribMask(Calculus):

    def _run(self, **kwargs):
        varname_dict = {'Biomass': 'Biomasse',
                        'Coal': 'Charbon',
                        'Gas': 'Gaz',
                        'HydroLake': 'Hydraulique lac',
                        'HydroSTEP': 'Hydraulique STEP',
                        'Nuclear': 'Nucléaire',
                        'Oil': 'Fioul et pointe',
                        'Waste': 'UIOM'}
        category = varname_dict[kwargs.get('category')]
        distrib_ini = self._cache.get_val('Supply:Dispatchable:Distribution:Ini')
        # distrib_frac = distrib_ini[category] / sum(distrib_ini[category])
        return distrib_ini[category] / 1e6


# class DispatchableParam(Calculus):

#     def _run(self, hyp_name=None, index=None, sumtot=None, mask=None, mydict=None, ret=None):
#         if sumtot > 0:
#             ret[mask, index] = ret[mask, index] * (my_dict['val'] - my_dict['sum']) / sumtot
#         else:
#             ret[mask, index] = (my_dict['val'] - my_dict['sum']) / mask.sum()
