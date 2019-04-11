import numpy as np

import Config.config as config
import babel.dot.initial_values as defcomp

from Utils.Numpy import div0
from Calculus.Initialisation.AsyncInit.asyncinit_entrypoint import Initialiser
from copy import deepcopy

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Residential(Initialiser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _compute(self, *args, **kwargs):
        geoindex = self.geo_indexes
        data = self.geocodes.copy()
        population = self._cache.get_val('population')

        # default values from _auto_paramdef that are indeed uniform for now in
        # METEOR
        ConstrCarac = self.searcher('Demand_Residential_Construction', 'NewConstrCarac')
        ConstrEner = self.searcher('Demand_Residential_Construction', 'NewConstrEner')
        ConstrDe = self.searcher('Demand_Residential_Construction', 'DeConstr')
        Renov49 = self.searcher('Demand_Residential_Renovation', 'Before49')
        Renov49_74 = self.searcher('Demand_Residential_Renovation', 'From49to74')
        Renov75_81 = self.searcher('Demand_Residential_Renovation', 'From75to81')
        Renov82_89 = self.searcher('Demand_Residential_Renovation', 'From82to89')
        Renov90_98 = self.searcher('Demand_Residential_Renovation', 'From90to98')
        Renov99_15 = self.searcher('Demand_Residential_Renovation', 'From99to15')
        ConsL = self.searcher('Demand_Residential_Consumption', 'Lighting')
        ConsCoo = self.searcher('Demand_Residential_Consumption', 'Cooking')
        ConsHt = self.filter_varname(self.searcher('Demand_Residential_Consumption', 'Heating'), 'technology')
        ConsECS = self.searcher('Demand_Residential_Consumption', 'Waterheating')
        ConsACt = self.filter_varname(self.searcher('Demand_Residential_Consumption', 'Airconditioning'), 'technology')
        ConsAir = self.searcher('Demand_Residential_Consumption', 'Airing')
        ConsEqi = self.filter_varname(self.searcher('Demand_Residential_Consumption', 'Equipments'), 'impact')
        simple_update_list = [ConstrCarac, ConstrEner, ConstrDe,
                              Renov49, Renov49_74, Renov75_81, Renov82_89, Renov90_98, Renov99_15,
                              ConsL, ConsCoo, ConsHt, ConsECS, ConsACt, ConsAir, ConsEqi]

        # default values from _auto_paramdef that are not uniform for now in
        # METEOR, i.e. that have to be changed here
        ConsHv = self.filter_varname(self.searcher('Demand_Residential_Consumption', 'Heating'), 'vector')
        ConsEqp = self.filter_varname(self.searcher('Demand_Residential_Consumption', 'Equipments'), 'possession')
        ConsACp = self.filter_varname(self.searcher('Demand_Residential_Consumption', 'Airconditioning'), 'penetration')

        # geolocalized data from cache
        propelants_narray = self._cache.get_val('Demand:Residential:Propelants').sum(axis=2)
        hvectordistrib = div0(propelants_narray, np.expand_dims(propelants_narray.sum(axis=2), axis=2))
        reffrac = propelants_narray.sum(axis=1) / np.expand_dims(propelants_narray.sum(axis=2).sum(axis=1), axis=1)
        # reffrac = np.round(reffrac, decimals=3)
        # idx_frac = np.argmax(reffrac, axis=1)
        # reffrac[:, idx_frac] -= reffrac.sum(axis=1) - 1
        eq_poss = self._cache.get_val('Demand:Residential:Equipments:Possession')
        ac_distrib = self._cache.get_val('Demand:Residential:Airconditioning:Distribution')

        # treat heat var to limit decimals while maintaining sum to 1 or 0
        # hvectorround = np.round(hvectordistrib, decimals=3)
        # hroundsum = hvectorround.sum(axis=2)
        # idx_0 = np.where(hroundsum > 0)
        # hmaxidx = np.argmax(hvectorround, axis=2)
        # hvectorround[idx_0[0], idx_0[1], hmaxidx[idx_0[0], idx_0[1]]] -= hroundsum[idx_0[0], idx_0[1]] - 1

        for geocode, population in zip(self.geo_list, self._cache.get_val('population')):
            # updating with uniform values
            for onecateg in simple_update_list:
                categc = deepcopy(onecateg)
                for key in categc.keys():
                    categc[key].update(
                        {'unit': 'base 100 en 2015',
                         'operation_type': ('mean', ''),
                         'metadata': {'Population du territoire': (int(population), 'sum')}})
                data[geocode].update(categc)

            # updating with geocode specific valuesc
            cConsHv = deepcopy(ConsHv)
            for key in cConsHv.keys():
                indices = self.find_idx(key, [['House', 'Apartment', 'Other'], defcomp.HEAT_ORDER])
                geoidx = self.geo_indexes[geocode]
                if hvectordistrib[geoidx, indices[0], :].sum() == 0:
                    myval = reffrac[geoidx, indices[1]]
                else:
                    myval = hvectordistrib[geoidx, indices[0], indices[1]]
                myval = myval * 100
                myn = propelants_narray[geoidx, indices[0], :].sum()
                myvars = ['de maisons', "d'appartements", "d'autres types de logements"]
                cConsHv[key].update(
                    {'default': myval,
                     'unit': 'base 100 en 2015',
                     'operation_type': ('mean', 'Nombre %s sur le territoire' % (myvars[indices[0]])),
                     'metadata': {'Population du territoire': (int(population), 'sum'),
                                  'Nombre %s sur le territoire' % (myvars[indices[0]]): (myn, 'sum')}})
            data[geocode].update(cConsHv)
            cConsEqp = deepcopy(ConsEqp)
            for key in cConsEqp.keys():
                indices = self.find_idx(key, [defcomp.EQ_ORDER])
                geoidx = self.geo_indexes[geocode]
                cConsEqp[key].update(
                    {'default': eq_poss[geoidx, indices[0]] * 100,
                     'unit': 'base 100 en 2015',
                     'operation_type': ('mean', ''),
                     'metadata': {'Population du territoire': (int(population), 'sum')}})
            data[geocode].update(cConsEqp)
            cConsACp = deepcopy(ConsACp)
            for key in cConsACp.keys():
                geoidx = self.geo_indexes[geocode]
                cConsACp[key].update(
                    {'default': ac_distrib[geoidx] * 100,
                     'unit': 'base 100 en 2015',
                     'operation_type': ('mean', ''),
                     'metadata': {'Population du territoire': (int(population), 'sum')}})
            data[geocode].update(cConsACp)
        return data
