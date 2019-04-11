

from Calculus.calculus import Calculus
import Config.config as config
from DB.Mongo.Mongo import Mongo

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class FranceCurveResultsVariables(Calculus):

    def _run(self, *args, **kwargs):
        varname = kwargs['variable']
        year = kwargs['year']
        simu_id = kwargs['simu_id']
        if __debug__:
            logger.debug("Try to recover variable %s from mongo in results-simulation id %s of year %s",
                         varname, simu_id, year)
        mongo = Mongo(database=config.MONGO_SIMULATIONS_DB, collection=simu_id)
        query = {'projection': 'curve_2', 'varname': varname, 'year': year}
        projection = {'FR99999': 1}
        if __debug__:
            logger.debug("Query to mongo: %s", query)
        cursor = mongo.find(query=query, projection=projection)

        return cursor[0]['FR99999']


class CurveMapResultsVariables(Calculus):

    def _run(self, *args, **kwargs):
        varname = kwargs['variable']
        year = kwargs['year']
        simu_id = kwargs['simu_id']
        proj = kwargs['projection']
        if __debug__:
            logger.debug("Try to recover variable %s from mongo in results-simulation id %s of year %s",
                         varname, simu_id, year)
        mongo = Mongo(database=config.MONGO_SIMULATIONS_DB, collection=simu_id)
        query = {'projection': proj, 'varname': varname, 'year': year}
        projection = {'projection': 0, 'varname': 0, 'year': 0, '_id': 0, 'timestamp': 0}
        if __debug__:
            logger.debug("Query to mongo: %s", query)
        cursor1 = mongo.find(query=query, projection=projection)
        return cursor1[0]
