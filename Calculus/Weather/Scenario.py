import numpy as np

import pickle

from DB.Mongo.Mongo import Mongo
from Calculus.calculus import Calculus
from Config.config import __NB_CALC_TEMPORAL_STEP__
import Config.variables as variables
import Config.config as config

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


def default_function_unpickle(cursor, varname, fieldforpickle='value'):
    if cursor.count() == 1:
        return pickle.loads(cursor[0][fieldforpickle])
    else:
        try:
            multi_val = list(range(cursor[0]["len"]))
            for i in range(cursor[0]["len"]):
                multi_val[cursor[i]["part"]] = cursor[i][fieldforpickle]
            myjoined = b''.join(multi_val)
            return pickle.loads(myjoined)
        except KeyError:
            if __debug__:
                logger.error('Mongo.get_val: More than one document found for variable = %s', varname)
            raise KeyError(varname, ' is not a valid key')


class RandomWeather(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we generate random scenarios
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, year, varname):
        # Return a random matrix
        nb_stations = len(self._cache.get_val("weather:stations"))
        nb_geocodes = len(self._cache.get_val("geocodes"))

        return (np.random.rand(nb_stations, __NB_CALC_TEMPORAL_STEP__).astype('float'),
                np.random.rand(nb_geocodes, nb_stations).astype('float'))


class SpecificYear(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_name = config.MONGODB_METEOR_DATABASE
        self.collections = {'base_year_numpy': 'weather.obs.interp.numpy'}
        self.collections.update({'interpolation_matrix': 'weather.interpolation_matrix'})
        self._mongo = Mongo(database=self.mongo_name)

    def _run(self, year, varname):
        query = {'variable': varname, 'year': year}
        tempcursor = self._mongo.find(query=query, collection=self.collections['base_year_numpy'])
        ret1 = default_function_unpickle(tempcursor, varname)
        query = {'variable': varname, 'type': 'interpolation_matrix'}
        tempcursor = self._mongo.find(query=query, collection=self.collections['interpolation_matrix'])
        ret2 = default_function_unpickle(tempcursor, varname)
        return ret1, ret2


class WeatherPick(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_name = config.MONGODB_METEOR_DATABASE
        self.collections = {'reconstructed_years_numpy': config.__WEATHER_COLLECTIONS__[7]}
        self.collections.update({'reconstructed_interpolation': config.__WEATHER_COLLECTIONS__[6]})
        self._mongo = Mongo(database=variables.config["common"]["mongo_db"])
        docs = self._mongo.find(query={}, database=self.mongo_name,
                                collection=self.collections['reconstructed_years_numpy'])
        self.reconstructed_choices = list(set([tuple(doc['year_build']) for doc in docs]))

    def _run(self, year, varname):
        np.random.seed(year[0].year)
        picked_reconstructed = list(self.reconstructed_choices[np.random.randint(0, len(self.reconstructed_choices))])
        query = {'year_build': picked_reconstructed, "variable": varname, "type": "reconstructed numpy"}
        tempcursor = self._mongo.find(query=query, database=self.mongo_name,
                                      collection=self.collections['reconstructed_years_numpy'])
        query = {'year_build': picked_reconstructed, "variable": varname, "type": "interpolation matrix"}
        tempcursor2 = self._mongo.find(query=query, database=self.mongo_name,
                                       collection=self.collections['reconstructed_interpolation'])
        ret1 = self._unpickle(tempcursor, varname)
        ret2 = self._unpickle(tempcursor2, varname)
        document = {'varname': 'weather_mix_id', 'value': picked_reconstructed,
                    'year': year, 'weather_variable': varname}
        self._mongo.insert(value=document, database=config.MONGO_SIMULATIONS_DB, collection=self._simu_id)
        return ret1, ret2

    def _unpickle(self, cursor, varname):
        ret = default_function_unpickle(cursor, varname)
        return ret
