import re
import numpy as np
import datetime
import pymongo
from pymongo import ASCENDING
from pymongo.cursor import Cursor as PymongoCursor
import csv

import Config.config as config
import Config.variables as variables
from Calculus.Initialisation.Initialisation import Initialisation
from Calculus.calculus import Calculus
import babel.dot.initial_values as defcomp
from Inputs.Csv.csv_reader import CsvReader
from Utils.Numpy import div0
from Data.DB.Mongo.mongo import Mongo


class Demand(Initialisation):

    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        # self._dispatcher = Dispatcher()
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE,
                            collection=config.__EMPLOYEES_COLLECTIONS__[0])


class MatricesDPE(Calculus):

    def _run(self):
        t1 = datetime.datetime.now()
        self.heatidx = {'Autres énergies': 3,
                        'Bois, Biomasse': 2,
                        'Electricité': 0,
                        'Gaz': 1,
                        "Production d'électricité": 4}
        self.dictpostal = {'80930': '80400'}
        filename = 'datas/csv/residential/dpe/DPE_GreenTech_noduplicates_yearonly.csv'
        reader = csv.reader(open(filename))
        geoidx = self._cache.get_val('geocodes_indexes')
        postal2idx = self.postal2idx()
        numbers = np.zeros((len(geoidx), 2, 6, 5))
        conso_tot = np.zeros((len(geoidx), 2, 6, 5))
        conso_heating = np.zeros((len(geoidx), 2, 6, 5))
        dpe = np.zeros((len(geoidx), 2, 6, 7))
        dpeconso = np.zeros((len(geoidx), 2, 6, 7))
        next(reader, None)
        count = 0
        count_pb = 0
        for row in reader:
            count += 1
            dateidx = self.dateidx(row[2])
            dpeidx = self.dpeidx(float(row[4]))
            heatidx = self.heatidx[row[10]]
            myrow = row[0].strip()
            try:
                temp = int(myrow)
            except ValueError:
                count_pb += 1
                # print('non numeric postal code %s' % (myrow))
                continue
            if len(myrow) < 5:
                count_pb += 1
                # print('non 5-digit postal code %s' % (myrow))
                continue
            try:
                mylen = len(postal2idx[myrow])
                myval = float(row[3]) * float(row[4]) / mylen
                dpe[postal2idx[myrow], int(row[1]) - 1, dateidx, dpeidx] += 1 / mylen
                dpeconso[postal2idx[myrow], int(row[1]) - 1, dateidx, dpeidx] += float(row[4]) / mylen
                # numbers[postal2idx[myrow], int(row[1]) - 1, dateidx, heatidx] += 1 / mylen
                # conso_tot[postal2idx[myrow], int(row[1]) - 1, dateidx, heatidx] += myval
                # conso_heating[postal2idx[myrow], int(row[1]) - 1, dateidx, heatidx] += float(row[11]) / mylen
            except KeyError:
                if myrow[0:2] != '97' and myrow[0:2] != '20':
                    if myrow in self.dictpostal:
                        myrow = self.dictpostal[myrow]
                    mylen = 1
                    try:
                        myidx = geoidx['FR' + myrow]
                    except KeyError:
                        count_pb += 1
                        # print('non postal code %s' % (myrow))
                        continue
                    myval = float(row[3]) * float(row[4]) / mylen
                    dpe[myidx, int(row[1]) - 1, dateidx, dpeidx] += 1 / mylen
                    dpeconso[myidx, int(row[1]) - 1, dateidx, dpeidx] += float(row[4]) / mylen
                    # numbers[myidx, int(row[1]) - 1, dateidx, heatidx] += 1 / mylen
                    # conso_tot[myidx, int(row[1]) - 1, dateidx, heatidx] += myval
                    # conso_heating[myidx, int(row[1]) - 1, dateidx, heatidx] += float(row[11]) / mylen
            except ValueError:
                count_pb += 1
                continue
        print('Problems %s / %s' % (count_pb, count))
        print('elapsed ', datetime.datetime.now() - t1)
        return dpe, dpeconso  # numbers, conso_heating, conso_tot

    def dpeidx(self, p):
        if int(p) < 50:
            return 0
        elif int(p) < 90:
            return 1
        elif int(p) < 150:
            return 2
        elif int(p) < 230:
            return 3
        elif int(p) < 330:
            return 4
        elif int(p) < 451:
            return 5
        else:
            return 6

    def dateidx(self, year):
        if int(year) < 1949:
            return 0
        elif int(year) < 1975:
            return 1
        elif int(year) < 1982:
            return 2
        elif int(year) < 1990:
            return 3
        elif int(year) < 1999:
            return 4
        else:
            return 5

    def postal2idx(self):
        self.mydict = {'49199': '49092',
                       '49303': '49018'}
        geoidx = self._cache.get_val('geocodes_indexes')
        postal2insee = self._cache.get_val('postal2insee')
        postal2idx = {}
        for postal in postal2insee:
            postal2idx[postal] = []
            for el in postal2insee[postal]:
                if 'FR' + el in geoidx:
                    postal2idx[postal].append(geoidx['FR' + el])
                elif el in self.mydict:
                    postal2idx[postal].append(geoidx['FR' + self.mydict[el]])
            if not postal2idx[postal]:
                if postal[0:2] == '97' or postal[0:2] == '20':
                    del postal2idx[postal]
                else:
                    print('Empty list for ', postal)
                    raise
        return postal2idx


class Postal2Insee(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE, collection=config.__GEOGRAPHICAL_COLLECTIONS__[1])

    def _run(self):
        docs = self._mongo.find(query={'type': 'postal2insee'})
        postal2insee = docs[0]['value']
        return postal2insee


class Insee2Postal(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE, collection=config.__GEOGRAPHICAL_COLLECTIONS__[1])

    def _run(self):
        docs = self._mongo.find(query={'type': 'insee2postal'})
        insee2postal = docs[0]['value']
        return insee2postal


class ResidentialConstants(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accomodation_types = ['1', '2', '3']
        self.room_number = ['1', '2', '3', '4', '5', '6']
        self.object_types = ['1', '2', '3', '4', '5', '6']
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE)

    def _res_insee_data(self):
        int_geo = self._cache.get_val('geocodes')
        index_geo = self._cache.get_val('geocodes_indexes')
        output = {}
        for collection in config.__RESIDENTIAL_COLLECTIONS__:
            varsuffix = collection.split('.')[-1]
            docs = self._mongo.find(query={}, collection=collection, sort=('geocode_insee', pymongo.ASCENDING))
            output[varsuffix] = np.zeros((len(int_geo), len(self.accomodation_types),
                                          len(self.room_number), len(self.object_types)))
            for doc in docs:
                output[varsuffix][index_geo[doc['geocode_insee']]] = self.__build_geo_array(doc)
            if varsuffix == 'propelants':
                heatgrid_mask = np.expand_dims(np.expand_dims(self.res_heatgrid_mask(
                    output[varsuffix].sum(axis=2).sum(axis=1)[:, 0]), axis=1), axis=2)
                non_heatgrid_mask = np.expand_dims(np.expand_dims(
                    self.res_non_heatgrid_mask(output[varsuffix].sum(axis=2).sum(axis=1)[:, 0]), axis=1), axis=2)
                output[varsuffix][:, :, :, 5] += non_heatgrid_mask * output[varsuffix][:, :, :, 0]
                output[varsuffix][:, :, :, 0] *= heatgrid_mask
            varname = 'Demand:Residential:' + varsuffix.capitalize()
            self._cache.set_val(varname, self.__rescale_data_to_2015(varname, output[varsuffix]))
        return None

    def __rescale_data_to_2015(self, obj, data):
        '''
        Returns rescaled values. The interface is such that it can at some point perform different rescalings
        for different variables. For now, the rescaling is performed on the basis of INSEE aggregate data on france
        for 2011 and 2015 (nb of residential buildings). This is applied to all 4 data sources, even when the data is
        from 2006, because our data seems closer to 2011 than 2006. To check at some point.
        '''
        hardcoded_growth_2011_2015 = 28909 / 28056
        return data * hardcoded_growth_2011_2015

    def __build_geo_array(self, doc):
        '''
        Very important : to access insee 2-4-2 we access array [1][3][1] because if not, we create a 4*7*7 array instead
        of 3*6*6 which means about 80percent too many empty values in memory
        '''
        ret = np.zeros((len(self.accomodation_types), len(self.room_number), len(self.object_types)))
        for key in doc.keys():
            try:
                ret[int(key[0]) - 1][int(key[2]) - 1][int(key[4]) - 1] = doc[key]
            except ValueError:
                pass
        return ret

    def _surfaces_by_constr_date(self):
        mean_surf = np.expand_dims(np.expand_dims(
            np.expand_dims(defcomp.MEAN_SURF_CAT, axis=0), axis=1), axis=2)
        surfaces = self._cache.get_val('Demand:Residential:Surfaces')
        surfaces_sum = np.sum(surfaces, axis=3)
        surfaces_by_room = div0(np.sum(surfaces * mean_surf, axis=3), surfaces_sum)
        constr_dates = self._cache.get_val('Demand:Residential:Construction_dates')
        surface_by_constr_date = constr_dates * np.expand_dims(surfaces_by_room, axis=3)
        self._cache.set_val('Demand:Residential:SqrtMeanSurfacesByRoom',
                            np.sqrt(np.expand_dims(surfaces_by_room, axis=3)))
        self._cache.set_val('Demand:Residential:SurfacesByConstrDate', surface_by_constr_date)
        return None

    def res_heatgrid_mask(self, heatgrid_insee_loc):
        heatgrid_loc = self._cache.get_val('heatgrid_loc')
        heatgrid_insee = np.zeros(heatgrid_insee_loc.shape)
        heatgrid_insee[heatgrid_insee_loc < defcomp.HEATGRID_CUTOFF_INSEE] = 0
        heatgrid_insee[heatgrid_insee_loc >= defcomp.HEATGRID_CUTOFF_INSEE] = 1
        heatgrid_combined = heatgrid_insee + heatgrid_loc
        heatgrid_combined[heatgrid_combined > 1] = 1
        return heatgrid_combined

    def res_non_heatgrid_mask(self, heatgrid_insee_loc):
        heatgrid_loc = self._cache.get_val('heatgrid_loc')
        non_heatgrid_insee = np.zeros(heatgrid_insee_loc.shape)
        non_heatgrid_insee[heatgrid_insee_loc > defcomp.HEATGRID_CUTOFF_INSEE] = 0
        non_heatgrid_insee[heatgrid_insee_loc > 0.5] = 1

        return non_heatgrid_insee

    def _run(self, *args, **kwargs):
        self._res_insee_data()
        self._surfaces_by_constr_date()
        return None


class ResidentialSecondaryConstants(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mongo = Mongo(database=config.MONGODB_METEOR_DATABASE,
                            collection=config.__RESIDENTIAL_SEC_COLLECTIONS__[0])

    def _run(self, *args, **kwargs):
        secondary = []
        sec_data = self._mongo.find(query={}, sort=('geocode_insee', pymongo.ASCENDING))
        for data in sec_data:
            secondary.append(float(data['value']))
        return np.array(secondary)


class TransportConstants(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _road_type_data(self):
        pass

    def _infrastructure_data(self):
        pass

    def _run(self, *args, **kwargs):
        self._road_type_data()
        self._infrastructure_data()
        return None
