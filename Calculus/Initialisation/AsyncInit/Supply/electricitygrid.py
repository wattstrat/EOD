import numpy as np

from Calculus.Initialisation.AsyncInit.asyncinit_entrypoint import Initialiser
import Config.variables as variables
import babel.dot.initial_values as defcomp


class CapasInit(Initialiser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _compute(self):
        _ = self.fatal_installed_capa()
        _ = self.dispatchable_installed_capa()
        return self.geocodes

    def fatal_installed_capa(self):
        wind_turbines_ini = self._cache.get_val('Supply:Wind:Turbines:Distribution:Ini',
                                                run_args=['Eolien_power_MW'])
        solar_distrib_ini = self._cache.get_val(
            'Supply:Solar:PV:Distribution:Ini', run_args=['Solaire photovoltaïque_power_MW'])
        hydro_distrib_ini = self._cache.get_val('Supply:HydroRun:Distrib:Ini')
        varnames = ['Supply_Electricitygrid_Fatal_HydroRun_All_power_hydrorun_powerchangemw',
                    'Supply_Electricitygrid_Fatal_PV_All_power_pv_powerchangemw',
                    'Supply_Electricitygrid_Fatal_Wind_All_power_wind_powerchangemw']
        varmax = {'Supply_Electricitygrid_Fatal_HydroRun_All_power_hydrorun_powerchangemw': 3,
                  'Supply_Electricitygrid_Fatal_PV_All_power_pv_powerchangemw': 20,
                  'Supply_Electricitygrid_Fatal_Wind_All_power_wind_powerchangemw': 10}
        vardata = [hydro_distrib_ini, solar_distrib_ini, wind_turbines_ini]
        for key, val in zip(varnames, vardata):
            for geocode, value in zip(self.geocodes.keys(), val):
                self.geocodes[geocode][key] = {'min': 0,
                                               'max': 500,
                                               'default': float(value) / 1e6,
                                               'unit': 'MW',
                                               'operation_type': ('sum', varmax[key]),
                                               'type': 'abs_val',
                                               'unit_label': 'puissance installée (MW - est. 2015)',
                                               'metadata': {}}
        return self.geocodes

    def dispatchable_installed_capa(self):
        dep_dict = {'Fioul et pointe': 'Oil',
                    'Charbon': 'Coal',
                    'Gaz': 'Gas',
                    'Nucléaire': 'Nuclear',
                    'Hydraulique lac': 'HydroLake',
                    'Hydraulique STEP': 'HydroSTEP',
                    'Biomasse': 'Biomass',
                    'UIOM': 'Waste',
                    }
        varmax = {'Fioul et pointe': 3,
                  'Charbon': 3,
                  'Gaz': 5,
                  'Nucléaire': 2,
                  'Hydraulique lac': 2,
                  'Hydraulique STEP': 2,
                  'Biomasse': 10,
                  'UIOM': 10,
                  }
        distrib_ini = self._cache.get_val('Supply:Dispatchable:Distribution:Ini')
        for myvar in set(distrib_ini.dtype.names) - {'Echphysiques'}:
            subdict = self.filter_varname(self.searcher(
                'Supply_Electricitygrid_Dispatchable', dep_dict[myvar]), 'power')
            varname = list(subdict.keys())[0]
            for geocode, value in zip(self.geocodes.keys(), distrib_ini[myvar]):
                self.geocodes[geocode][varname] = {'min': 0,
                                                   'max': float(distrib_ini[myvar].max() / 1e6 * 3),
                                                   'default': float(value) / 1e6,
                                                   'unit': 'MW',
                                                   'operation_type': ('sum', varmax[myvar]),
                                                   'type': 'abs_val',
                                                   'unit_label': 'puissance installée (MW - est. 2015)',
                                                   'metadata': {}}
        return self.geocodes
