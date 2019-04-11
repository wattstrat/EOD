import Config.config as config
import babel.dot.initial_values as defcomp
from Calculus.Initialisation.AsyncInit.asyncinit_entrypoint import Initialiser
from copy import deepcopy

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Industry(Initialiser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _compute(self, *args, **kwargs):
        geoindex = self.geo_indexes
        data = self.geocodes.copy()
        employees = self._cache.get_val('Demand:Industry:Employees:Ini')
        ProdInd = self.searcher('Demand_Industry_Activity', 'Activity')
        IndEff = self.searcher('Demand_Industry_Consumption', 'Efficiency')
        simple_update_list = [(ProdInd, 4),
                              (IndEff, -3)]

        for geocode, population in zip(self.geo_list, self._cache.get_val('population')):
            for onecateg, idx in simple_update_list:
                categc = deepcopy(onecateg)
                for key in categc.keys():
                    employees_number = employees[geoindex[geocode]][defcomp.IND_DICT_REV[key.split('_')[idx]]]
                    labelkey = defcomp.DICT_NAF_TO_IND[key.split('_')[idx]]
                    employeesmax = employees[:, defcomp.IND_DICT_REV[key.split('_')[idx]]].max()
                    if 'nb_empl' in key:
                        tempdict = {'min': 0,
                                    'max': 3 * employeesmax,
                                    'default': int(employees_number),
                                    'unit': 'nombre d\'ETP',
                                    'operation_type': ('sum', 3),
                                    'type': 'abs_val',
                                    'unit_label': 'nombre d\'ETP',
                                    'metadata': {'Salariés de la branche ' + labelkey: (int(employees_number), 'sum'),
                                                 'Population du territoire': (int(population), 'sum')}}
                    else:
                        tempdict = {'unit': 'base 100 en 2015',
                                    'operation_type': ('mean', ''),
                                    'metadata': {'Salariés de la branche ' + labelkey: (int(employees_number), 'sum'),
                                                 'Population du territoire': (int(population), 'sum')}}

                    categc[key].update(tempdict)
                data[geocode].update(categc)
        return data
