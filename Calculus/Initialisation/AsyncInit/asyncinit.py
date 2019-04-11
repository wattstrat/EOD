import logging.config

import Config.config as config
from DB.Mongo.Mongo import Mongo
from Calculus.calculus import Calculus

import random
import string


class SaasConfig(Calculus):

    def _run(self, *args, **kwargs):
        replace = kwargs.get("replaceCollection", False)

        perfArgs = {}

        if "init_db" in kwargs:
            perfArgs["init_db"] = kwargs["init_db"]
        else:
            perfArgs["init_db"] = config.MONGODB_INIT_DB

        if "init_collection" in kwargs:
            perfArgs["init_collection"] = kwargs["init_collection"]
        elif replace:
            perfArgs["init_collection"] = config.__INIT_COLLECTIONS__[
                'main'] + ''.join(random.choices(string.ascii_uppercase, k=6))

        calc = self.calculus('Calculus.Initialisation.AsyncInit.asyncinit_entrypoint.PerformInsertion', **perfArgs)

        ret = calc()

        if replace and perfArgs["init_collection"] != config.__INIT_COLLECTIONS__['main']:
            init_mongo = {'database': perfArgs["init_db"], 'collection': config.__INIT_COLLECTIONS__['main']}
            saasconfig_mongo = Mongo(**init_mongo)
            saasconfig_mongo.drop_collection(config.__INIT_COLLECTIONS__['main'])
            init_mongo = {'database': perfArgs["init_db"], 'collection': perfArgs["init_collection"]}
            saasconfig_mongo = Mongo(**init_mongo)
            saasconfig_mongo.rename_collection(config.__INIT_COLLECTIONS__['main'])

        return ret
