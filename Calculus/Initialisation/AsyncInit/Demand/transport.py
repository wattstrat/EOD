import Config.config as config
import babel.dot.initial_values as defcomp
from Calculus.Initialisation.AsyncInit.asyncinit_entrypoint import Initialiser
from copy import deepcopy

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Transport(Initialiser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def findidx(self, key, mytypes, mysubtypes):
        for i, el1 in enumerate(mytypes):
            if el1 in key:
                break
        for j, el2 in enumerate(mysubtypes):
            if el2 in key:
                break
        return i * len(mysubtypes) + j, i

    def _compute(self, *args, **kwargs):
        geoindex = self.geo_indexes
        data = self.geocodes.copy()
        totpopulation = self._cache.get_val('population')
        FreightTraffic = self.searcher('Demand_Transport_Freight', 'Traffic')
        FreightConsA = self.searcher('Demand_Transport_Freight', 'Consumption_Air')
        FreightConsRa = self.searcher('Demand_Transport_Freight', 'Consumption_Rail')
        FreightConsRo = self.searcher('Demand_Transport_Freight', 'Consumption_Road')
        PeopleMob = self.searcher('Demand_Transport_People', 'Mobility')
        PeopleConsA = self.searcher('Demand_Transport_People', 'Consumption_Air')
        PeopleConsRa = self.searcher('Demand_Transport_People', 'Consumption_Rail')
        PeopleConsRo = self.searcher('Demand_Transport_People', 'Consumption_Road')
        Infra = self.searcher('Demand_Transport_Infrastructure', 'Infrastructure')
        simple_update_list = [FreightTraffic, FreightConsA, FreightConsRa,
                              PeopleMob, PeopleConsA, PeopleConsRa]
        froad_types = ['vul', 'truck']
        froad_fr = ["d'utilitaires", 'de camions']
        froad_energy_types = ['petroleum_oil', 'petroleum_diesel', 'gasgrid', 'petroleum_semi-elec', 'electricitygrid']
        fontheroad = self._cache.get_val('ontheroadfullf')

        proad_vehicles = ['car', 'vul', 'bus']
        proad_fr = ['de voitures', 'de VUL', 'de bus']
        proad_energy_types = ['petroleum_oil', 'petroleum_diesel', 'gasgrid', 'petroleum_semi-elec', 'electricitygrid']
        pontheroad = self._cache.get_val('ontheroadfullp')

        Nairport = self._cache.get_val('n_airport')
        Ntrain = self._cache.get_val('n_train_station')
        Nparking = self._cache.get_val('n_parking')
        KMroad = self._cache.get_val('km_road')
        KMhighway = self._cache.get_val('km_highway')
        train_max = Ntrain.max()
        airp_max = Nairport.max()
        park_max = Nparking.max()
        road_max = KMroad.max()
        high_max = KMhighway.max()
        infravars = {'Demand_Transport_Infrastructure_Infrastructure_All_infrastructure_airport': (Nairport, airp_max, "Nombre d'aéroports"),
                     'Demand_Transport_Infrastructure_Infrastructure_All_infrastructure_trainstation': (Ntrain, train_max, "Nombre de gares ferroviaires"),
                     'Demand_Transport_Infrastructure_Infrastructure_All_infrastructure_road': (KMroad, road_max, 'Km de route'),
                     'Demand_Transport_Infrastructure_Infrastructure_All_infrastructure_highway': (KMhighway, high_max, "Km d'autoroute"),
                     'Demand_Transport_Infrastructure_Infrastructure_All_infrastructure_parking': (Nparking, park_max, 'Nombre de logements équipés de places de parking'),
                     }

        for geocode, population in zip(self.geo_list, totpopulation):
            geoidx = geoindex[geocode]
            for onecateg in simple_update_list:
                categc = deepcopy(onecateg)
                for key in categc.keys():
                    categc[key].update(
                        {'unit': 'base 100 en 2015',
                         'operation_type': ('mean', ''),
                         'metadata': {'Population du territoire': (int(population), 'sum')}})
                data[geocode].update(categc)
            categc = deepcopy(Infra)
            for key in categc.keys():
                if key not in infravars:
                    categc[key].update(
                        {'unit': 'base 100 en 2015',
                         'operation_type': ('mean', ''),
                         'metadata': {'Population du territoire': (int(population), 'sum')}})
                else:
                    categc[key].update(
                        {'min': 0,
                         'max': 3 * infravars[key][1],
                         'default': infravars[key][0][geoidx],
                         'operation_type': ('sum', 3),
                         'type': 'abs_val',
                         'unit_label': infravars[key][2],
                         'unit': 'nombre en 2014',
                         'metadata': {'Population du territoire': (int(population), 'sum')}})
            data[geocode].update(categc)
            categc = deepcopy(FreightConsRo)
            for key in categc.keys():
                if 'mix' not in key:
                    categc[key].update(
                        {'unit': 'efficacité énergétique, chiffres nationaux',
                         'operation_type': ('mean', ''),
                         'metadata': {'Population du territoire': (int(population), 'sum')}})
                else:
                    idx1, idx2 = self.findidx(key, froad_types, froad_energy_types)
                    sumval = fontheroad[geoidx, idx1 - idx1 % 5:idx1 - idx1 % 5 + 5].sum()
                    categc[key].update(
                        {'min': 0,
                         'max': 100,
                         'default': fontheroad[geoidx, idx1] / sumval * 100,
                         'operation_type': ('mean', 'Nombre %s' % (froad_fr[idx2])),
                         'type': 'percent_repartition',
                         'unit_label': 'Mix énergétique en pourcent',
                         'unit': 'percent',
                         'metadata': {'Population du territoire': (int(population), 'sum'),
                                      'Nombre %s' % (froad_fr[idx2]): (sumval, 'sum')}})
            data[geocode].update(categc)
            categc = deepcopy(PeopleConsRo)
            for key in categc.keys():
                if 'mix' not in key:
                    categc[key].update(
                        {'unit': 'efficacité énergétique, chiffres nationaux',
                         'operation_type': ('mean', ''),
                         'metadata': {'Population du territoire': (int(population), 'sum')}})
                else:
                    idx1, idx2 = self.findidx(key, proad_vehicles, proad_energy_types)
                    sumval = pontheroad[geoidx, idx1 - idx1 % 5:idx1 - idx1 % 5 + 5].sum()
                    categc[key].update(
                        {'min': 0,
                         'max': 100,
                         'default': pontheroad[geoidx, idx1] / sumval * 100,
                         'operation_type': ('mean', 'Nombre %s' % (proad_fr[idx2])),
                         'type': 'percent_repartition',
                         'unit_label': 'Mix énergétique en pourcent',
                         'unit': 'percent',
                         'metadata': {'Population du territoire': (int(population), 'sum'),
                                      'Nombre %s' % (proad_fr[idx2]): (sumval, 'sum')}})
            data[geocode].update(categc)
        return data
