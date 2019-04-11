import Config.config as config
import babel.dot.initial_values as defcomp
from babel.dot.translator import TRANSLATOR

from Calculus.Initialisation.AsyncInit.asyncinit_entrypoint import Initialiser
from copy import deepcopy
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Tertiary(Initialiser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def localutility(self, key, employees, geoindex, geocode, idx):
        temp1 = defcomp.DICT_TER_TO_NAF[key.split('_')[idx]]
        mylist = [employees[geoindex[geocode]][defcomp.TER_DICT_REV[temp1[i]]] for i in range(len(temp1))]
        return sum(mylist)

    def _compute(self, *args, **kwargs):
        geoindex = self.geo_indexes
        data = self.geocodes.copy()
        employees = self._cache.get_val('Demand:Tertiary:Employees:Ini')
        population = self._cache.get_val('population')
        TerConstr = self.searcher('Demand_Tertiary_Construction', 'Surfaces')
        TerRenov = self.searcher('Demand_Tertiary_Renovation', 'Thermal')
        TerConsSU = self.searcher('Demand_Tertiary_Consumption', 'Specificuse')
        TerConsH = self.searcher('Demand_Tertiary_Consumption', 'Heating')  # a faire
        # ajouter un % du tertiaire equipé d'ac ?
        TerConsAC = self.searcher('Demand_Tertiary_Consumption', 'Airconditioning')
        TerConsL = self.searcher('Demand_Tertiary_Consumption', 'Lighting')
        simple_update_list = [(TerConstr, -4),
                              (TerRenov, -3),
                              (TerConsSU, -6),
                              (TerConsAC, -5),
                              (TerConsL, -5), ]
        heatpct = self._cache.get_val('Demand:Tertiary:PctHeat:Ini')
        acpct = self._cache.get_val('Demand:Tertiary:ACFrac:Ini')

        for geocode, population in zip(self.geo_list, self._cache.get_val('population')):
            for onecateg, refidx in simple_update_list:
                categc = deepcopy(onecateg)
                for key in categc.keys():
                    employees_number = self.localutility(key, employees, geoindex, geocode, refidx)
                    tempdict = {'unit': 'base 100 en 2015',
                                'operation_type': ('mean', ''),
                                'metadata': {'Salariés ' + TRANSLATOR[key.split('_')[refidx]]: (int(employees_number), 'sum'),
                                             'Population du territoire': (int(population), 'sum')}}
                    if 'Demand_Tertiary_Construction_Surfaces' in key and 'ac_surfaces' in key:
                        idx = [el in key for el in defcomp.TER_ORDER].index(True)
                        tempdict['operation_type'] = ('mean', 'Salariés ' + TRANSLATOR[key.split('_')[refidx]])
                        tempdict['default'] = acpct[geoindex[geocode], idx] * 100
                        tempdict['max'] = 100
                        tempdict['min'] = 0
                        tempdict['unit'] = 'pourcentage'
                    elif 'Demand_Tertiary_Construction_Surfaces' in key and 'heated_surfaces' in key:
                        idx = [el in key for el in defcomp.TER_ORDER].index(True)
                        tempdict['operation_type'] = ('mean', 'Salariés ' + TRANSLATOR[key.split('_')[refidx]])
                        tempdict['default'] = heatpct[idx] * 100
                        tempdict['max'] = 100
                        tempdict['min'] = 0
                        tempdict['unit'] = 'pourcentage'
                    categc[key].update(tempdict)
                data[geocode].update(categc)
            cTerConsH = deepcopy(TerConsH)
            for key in cTerConsH.keys():
                if 'technology' in key:
                    idx = -6
                elif 'vector' in key:
                    idx = -5
                employees_number = self.localutility(key, employees, geoindex, geocode, idx)
                cTerConsH[key].update(
                    {'unit': 'base 100 en 2015',
                     'operation_type': ('mean', ''),
                     'metadata': {'Salariés ' + TRANSLATOR[key.split('_')[idx]]: (int(employees_number), 'sum'),
                                  'Population du territoire': (int(population), 'sum')}})
            data[geocode].update(cTerConsH)
        return data
