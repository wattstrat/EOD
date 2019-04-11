import numpy as np

from Calculus.Initialisation.AsyncInit.asyncinit_entrypoint import Initialiser
import Config.variables as variables
import babel.dot.initial_values as defcomp
from babel.dot.other_outputs import HEAT_SOURCES
import Config.config as config


class PropLossesInit(Initialiser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _compute(self):
        self.prop_distrib_losses()
        return self.geocodes

    def prop_distrib_losses(self):
        prop_ini = self._cache.get_val('Supply:Heatgrid:Propelant:Distrib:Ini')
        losses_ini = self._cache.get_val('Supply:Heatgrid:Propelant:Losses:Ini')
        order = self._cache.get_val('Hypothesis:Default:Order')
        populations = self._cache.get_val('population')
        refmaps = self.refmaps2015('Summary_Heatgrid_Consumption')
        prefix = 'Supply_Heatgrid_Production_Production'
        for suffix in order[prefix]:
            idx = HEAT_SOURCES.index(suffix.replace('mix_power_', ''))
            for geocode in self.geocodes:
                varname = prefix + '_' + suffix
                value = prop_ini[self.geo_indexes[geocode], idx] - config.NONZERO_VAL
                population = populations[self.geo_indexes[geocode]]
                myconso = refmaps[geocode]
                tempdict = {'min': 0,
                            'max': 100,
                            'default': float(value) * 100,
                            'unit': '%% en 2015',
                            'operation_type': ('mean', 'Consommation de chaleur indicative (MWh - 2015)'),
                            'type': 'percent_repartition',
                            'unit_label': 'Répartition des combustibles du réseau de chaleur',
                            'metadata': {'Population du territoire': (int(population), 'sum'),
                                         'Consommation de chaleur indicative (MWh - 2015)': (myconso[0] / 1e6, 'sum')}
                            }
                self.geocodes[geocode][varname] = tempdict
        for geocode in self.geocodes:
            varname = 'Supply_Heatgrid_Grid_Losses_technical_on_grid'
            value = losses_ini[self.geo_indexes[geocode], :-1].mean()
            population = populations[self.geo_indexes[geocode]]
            myconso = refmaps[geocode]
            tempdict = {'min': 0,
                        'max': 100,
                        'default': (float(value) - 1) * 100,
                        'unit': '%% en 2015',
                        'operation_type': ('mean', 'Consommation de chaleur indicative (MWh - 2015)'),
                        'type': 'coef',
                        'unit_label': 'Pertes sur le réseau de chaleur',
                        'metadata': {'Population du territoire': (int(population), 'sum'),
                                     'Consommation de chaleur indicative (MWh - 2015)': (myconso[0] / 1e6, 'sum')}
                        }
            self.geocodes[geocode][varname] = tempdict
        return self.geocodes

    def refmaps2015(self, varname):
        ret = {}
        refsimu = 'bilan2015'
        refyear = 2015
        for proj in ['map_1', 'map_2']:
            maps = self._cache.get_val(
                'SimulationResultVariable:%s:%d:%s:%s' % (refsimu, refyear, varname, proj),
                run_kwargs={'simu_id': refsimu, 'year': refyear,
                            'projection': proj, 'variable': varname},
                method='Calculus.QueryMongo.SimulationVariables.CurveMapResultsVariables'
            )
            ret.update(maps)
        return ret
