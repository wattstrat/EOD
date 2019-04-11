
from Inputs.inputs import Inputs
import Config.variables as variables
import Config.config as config

if __debug__:
    import logging
    logger = logging.getLogger(__loader__.name)

"""
    This class represent the METEOR databases interface.
    All databases classes inherit to this class.
    TODO
    abstract code duplication
"""


class DB(Inputs):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_name = None
        self.collections = {}
        self.collections['reconstructed_years'] = None
        self.collections['weather_data'] = None

    def get_sets(self, *args, **kwargs):
        '''
        Collection in a db, build the sets of stations, years and variables available, and the list of these triplets.
        '''
        database = kwargs.get('database', self.mongo_name)
        collection = kwargs.get('collection', self.collections['weather_data'])
        if __debug__:
            logger.debug('Look for all documents in DB %s and collection %s', database, collection)
        docs = self._mongo.find(query={}, database=database, collection=collection)
        stations_set = set()
        year_set = set()
        variable_set = set()
        doc_keys = []
        docs_dict = {}
        stations_set_by_var = {}
        for doc in docs:
            if doc['variable'] not in stations_set_by_var.keys():
                stations_set_by_var[doc['variable']] = {doc["station"]}
            else:
                stations_set_by_var[doc['variable']].update({doc["station"]})
            stations_set.update([doc["station"]])
            year_set.update([doc["year"]])
            variable_set.update([doc["variable"]])
            doc_keys.append([doc["station"], doc["year"], doc["variable"]])
            try:
                docs_dict[doc["station"]][doc["variable"]].update({doc["year"]})
            except KeyError:
                try:
                    docs_dict[doc["station"]].update({doc["variable"]: {doc["year"]}})
                except KeyError:
                    docs_dict[doc["station"]] = {doc["variable"]: {doc["year"]}}
        self.years_set = year_set
        self.variables_set = variable_set
        self.stations_set = stations_set
        self.list_docs = doc_keys
        self.stations_set_by_var = stations_set_by_var

    def get_sets_for_randomization(self, *args, **kwargs):
        '''
        Build the weather variables for which there is more than 2 year of interpolated data in common
        '''
        database = kwargs.get('database', self.mongo_name)
        collection = kwargs.get('collection', self.collections['weather_data'])
        self.get_sets(database=database, collection=collection)
        self.available_years_per_var = {var: set() for var in self.variables_set}
        for doc in self.list_docs:
            self.available_years_per_var[doc[2]].update({doc[1]})
        for var in self.available_years_per_var.keys():
            if len(self.available_years_per_var[var]) < 2:
                self.variables_set.discard(var)
        list_set_years = [self.available_years_per_var[var] for var in self.variables_set]
        self.intersection_available_years = set.intersection(*list_set_years)
        self.available_for_randomization = {}
        if len(self.intersection_available_years) > 1:
            self.available_for_randomization = {var: self.intersection_available_years for var in self.variables_set}

    def get_sets_reconstruction(self, *args, **kwargs):
        '''
        From a db and a collection, sets of keys
        '''
        database = kwargs.get('database', self.mongo_name)
        collection = kwargs.get('collection', self.collections['reconstructed_years'])
        if __debug__:
            logger.debug('Look for all documents in DB %s and collection %s', database, collection)
        docs = self._mongo.find(query={}, database=database, collection=collection)
        self.variable_set = set()
        self.stations_set = set()
        self.year_build_set = set()
        for doc in docs:
            self.variable_set.update({doc['variable']})
            self.stations_set.update({doc['station']})
            self.year_build_set.update({str(doc['year_build'])})

    # ugly code duplication - quick and dirty
    def get_sets_reconstruction_numpy(self, *args, **kwargs):
        '''
        From a db and a collection, sets of keys
        '''
        database = kwargs.get('database', self.mongo_name)
        collection = kwargs.get('collection', self.collections['reconstructed_years'])
        if __debug__:
            logger.debug('Look for all documents in DB %s and collection %s', database, collection)
        docs = self._mongo.find(query={}, database=database, collection=collection)
        self.variable_set = set()
        self.year_build_set = set()
        for doc in docs:
            self.variable_set.update({doc['variable']})
            self.year_build_set.update({str(doc['year_build'])})
