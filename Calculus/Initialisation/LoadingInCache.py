import pymongo
import numpy as np
import csv

import Config.variables as variables
import Config.config as config
from Inputs.Csv.csv_reader import CsvReader

from Calculus.calculus import Calculus
from DB.Mongo.Mongo import Mongo

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class GeocodeInsee(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE, collection=config.__GEOCODES_COLLECTIONS__[0])

    def _run(self, *args, **kwargs):
        # Get geocodes and all associated fields from MONGO_REF, possibly multiple collections
        docs = self._mongo.find(query={}, sort=('geocode_insee', pymongo.ASCENDING))
        # for each of those collections, build a list of only the geocodes, and put them in a list of lists
        geocodes = []
        populations = []
        positions = []
        surfaces = []
        for doc in docs:
            geocodes.append(doc['geocode_insee'])
            populations.append(float(doc['population']))
            positions.append([doc['longitude_radian'], doc['latitude_radian']])
            surfaces.extend([float(doc['surface'])])
        geocodes_indexes = {el: i for i, el in enumerate(geocodes)}
        # set those values
        self._cache.set_val('geocodes', geocodes)
        self._cache.set_val('population', populations)
        self._cache.set_val('geocodes_indexes', geocodes_indexes)
        self._cache.set_val('position', np.array(positions))
        self._cache.set_val('surface', surfaces)
        return None


class Roughness(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE, collection=config.__GEOGRAPHICAL_COLLECTIONS__[0])

    def _run(self, *args, **kwargs):
        geocodes_indexes = self._cache.get_val('geocodes_indexes')
        docs = self._mongo.find(query={"variable": "CLC data"})
        roughness = np.zeros((len(geocodes_indexes), 1))
        corine_raw = [None] * len(geocodes_indexes)
        for doc in docs:
            roughness[geocodes_indexes[doc['geocode_insee']]] = doc['roughness']
            corine_raw[geocodes_indexes[doc['geocode_insee']]] = doc['data']
        self._cache.set_val('roughness', roughness)
        self._cache.set_val('corine_raw', corine_raw)
        if roughness.min() == 0:
            if __debug__:
                logger.warning('Be advised, roughness is treated as a multiplicative hypothesis, '
                               'but there are some geocodes with an average roughness of 0, '
                               'therefore any change by the user to this geocode cannot be taken into account')
        return None


class WeightsCorine(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = 'datas/csv/geographical/CORINE land cover - nomenclatura.csv'

    def _run(self, *args, **kwargs):
        with open(self.filename, 'r') as reader:
            lines = csv.reader(reader, delimiter=';')
            next(lines, None)
            pvweights = []
            for line in lines:
                pvweights.append(float(line[4]))
        self._cache.set_val('PV:corine:weights', pvweights)
        return None


class WeatherLongTerm(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE, collection=config.__WEATHER_COLLECTIONS__[9])

    def _run(self, *args, **kwargs):
        mean20160, std20160 = self.multi_docs_unpack(
            'AverageWind', 'combination of weibull and replacement 20-160m', 'mean', 'std', counties=False)
        mean10, std10 = self.multi_docs_unpack('AverageWind', 'raw 10m', 'mean', 'std', counties=True)
        mean_lum, std_lum = self.multi_docs_unpack('Luminosity', 'raw 10m', 'mean', 'std', counties=True)
        distrib = self.multi_docs_unpack('AverageWind', 'distrib 10m', 'distrib', counties=True)
        docs = self._mongo.find(query={'type': 'distrib 10m', 'variable': 'AverageWind', 'county': 'FR99201'})
        xaxis = np.array(docs[0]['xaxis distrib'])
        self._cache.set_val('Wind:Longterm:20160:mean', mean20160)
        self._cache.set_val('Wind:Longterm:20160:std', std20160)
        self._cache.set_val('Wind:Longterm:10:mean', mean10)
        self._cache.set_val('Wind:Longterm:10:std', std10)
        self._cache.set_val('Wind:Longterm:10:distrib', distrib)
        self._cache.set_val('Wind:Longterm:10:xaxis', xaxis)
        self._cache.set_val('Lum:Longterm:10:mean', mean_lum)
        self._cache.set_val('Lum:Longterm:10:std', std_lum)
        return None

    def multi_docs_unpack(self, myvar, mytype, *args, counties=True):
        counties_indexes = self._cache.get_val('counties_indexes').copy()
        del counties_indexes['FR99999']
        ordered_counties = sorted(list(counties_indexes.keys()))
        ret = []
        for i in range(len(args)):
            ret.append([])
        if counties:
            for key in counties_indexes:
                docs = self._mongo.find(query={'type': mytype, 'variable': myvar, 'county': key})
                for idx, myarg in enumerate(args):
                    ret[idx].extend(docs[0][myarg])
        else:
            docs = self._mongo.find(query={'type': mytype, 'variable': myvar})
            for idx, myarg in enumerate(args):
                ret[idx].extend(docs[0][myarg])
        for idx, el in enumerate(ret):
            ret[idx] = np.array(el)
            if len(ret[idx].shape) == 1:
                ret[idx] = np.expand_dims(ret[idx], axis=1)
        if len(ret) == 1:
            return ret[0]
        else:
            return ret


class Counties(Calculus):

    def _run(self, *args, **kwargs):
        # get counties indexes
        countiesind_method = 'Calculus.Initialisation.LoadingInCache.CountiesIndexes'
        countiesind = self._cache.get_val('counties_indexes', method=countiesind_method)

        return sorted(countiesind.keys())


class CountiesIndexes(Calculus):

    def _run(self, *args, **kwargs):
        # get geocodes
        geocodes = self._cache.get_val('geocodes')
        # build dictionnary that for each county gives the corresponding starting
        # and ending indices in list of geocodes
        current_cty = 'FR992' + geocodes[0][2:4]
        cty_idx = {current_cty: {'start': 0}}
        for i, geocode in enumerate(geocodes):
            temp_cty = 'FR992' + geocode[2:4]
            if temp_cty != current_cty:
                cty_idx[current_cty]['end'] = i
                current_cty = temp_cty
                cty_idx[current_cty] = {'start': i}
        cty_idx[current_cty]['end'] = i + 1
        cty_idx['FR99999'] = {'start': 0, 'end': i + 1}
        return cty_idx


class CountiesToRegions(Calculus):

    def _run(self, *args, **kwargs):
        ctyreg = {1: 82, 2: 22, 3: 83, 4: 93, 5: 93, 6: 93, 7: 82, 8: 21, 9: 73, 10: 21, 11: 91,
                  12: 73, 13: 93, 14: 25, 15: 83, 16: 54, 17: 54, 18: 24, 19: 74, 21: 26, 22: 53,
                  23: 74, 24: 72, 25: 43, 26: 82, 27: 23, 28: 24, 29: 53, 30: 91, 31: 73, 32: 73,
                  33: 72, 34: 91, 35: 53, 36: 24, 37: 24, 38: 82, 39: 43, 40: 72, 41: 24, 42: 82,
                  43: 83, 44: 52, 45: 24, 46: 73, 47: 72, 48: 91, 49: 52, 50: 25, 51: 21, 52: 21,
                  53: 52, 54: 41, 55: 41, 56: 53, 57: 41, 58: 26, 59: 31, 60: 22, 61: 25, 62: 31,
                  63: 83, 64: 72, 65: 73, 66: 91, 67: 42, 68: 42, 69: 82, 70: 43, 71: 26, 72: 52,
                  73: 82, 74: 82, 75: 11, 76: 23, 77: 11, 78: 11, 79: 54, 80: 22, 81: 73, 82: 73,
                  83: 93, 84: 93, 85: 52, 86: 54, 87: 74, 88: 41, 89: 26, 90: 43, 91: 11, 92: 11,
                  93: 11, 94: 11, 95: 11}
        return ctyreg


class RegionIndustryFraction(Calculus):

    def _run(self, *args, **kwargs):
        region_proportion_ind_conso = {11: 5.04895886483466,
                                       21: 3.0808853900916,
                                       22: 4.20827562747528,
                                       23: 7.3717715090993,
                                       24: 2.49046334766868,
                                       25: 1.55988045775931,
                                       26: 1.73239060184173,
                                       31: 15.3752703063877,
                                       41: 8.81502539057754,
                                       42: 3.90456058507666,
                                       43: 1.90733046626333,
                                       52: 3.21937944942537,
                                       53: 2.53905775445246,
                                       54: 2.10413781373764,
                                       72: 5.46687076317516,
                                       73: 2.63381684768083,
                                       74: 1.46755108487013,
                                       82: 13.1617950773866,
                                       83: 1.6060451442039,
                                       91: 1.50156716961878,
                                       93: 10.8049663483733}
        return region_proportion_ind_conso


class RegionIndustryFromEmployees(Calculus):

    def _run(self, *args, **kwargs):
        geos = self._cache.get_val('geocodes')
        cty_idx = self._cache.get_val('counties_indexes')
        employees_conso = (self._cache.get_val('Demand:Industry:EmployeesConsumptions')).sum(axis=1)
        employees = self._cache.get_val('Demand:Industry:Employees:Ini')
        cty_to_region = self._cache.get_val('counties_to_regions')
        ret = {}
        for county, vals in cty_idx.items():
            if county != 'FR99999':
                cty = int(county[5:])
                cty_sum_empl = employees[vals['start']:vals['end'], :].sum(axis=0)
                ret[cty_to_region[cty]] = ret.get(cty_to_region[cty], 0) + cty_sum_empl
        sumtot = 0
        for reg in ret:
            ret[reg] = (ret[reg] * employees_conso).sum()
            sumtot += ret[reg]
        return {key: val / sumtot * 100 for key, val in ret.items()}


class DynamicResidential(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE,
                            collection=config.__RESIDENTIAL_DYN_COLLECTIONS__[0])

    def _run(self, *args, **kwargs):
        docs = self._mongo.find(query={}, projection={'_id': 0})
        dayvalue = list(range(364))
        for doc in docs:
            dayn = int(list(doc.keys())[0])
            dayvalue[dayn] = doc[list(doc.keys())[0]]
        return dayvalue


class FrenchTourists(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE,
                            collection=config.__RESIDENTIAL_DYN_COLLECTIONS__[1])

    def _run(self, *args, **kwargs):
        docs = self._mongo.find(query={}, projection={'_id': 0})
        dayvalue = list(range(364))
        for doc in docs:
            dayn = int(list(doc.keys())[0])
            dayvalue[dayn] = doc[list(doc.keys())[0]]
        return dayvalue


class ForeignTourists(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE,
                            collection=config.__RESIDENTIAL_DYN_COLLECTIONS__[2])

    def _run(self, *args, **kwargs):
        docs = self._mongo.find(query={}, projection={'_id': 0})
        dayvalue = list(range(364))
        for doc in docs:
            dayn = int(list(doc.keys())[0])
            dayvalue[dayn] = doc[list(doc.keys())[0]]
        return dayvalue
