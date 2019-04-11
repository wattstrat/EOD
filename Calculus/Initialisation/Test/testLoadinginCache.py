import unittest
import random
import Config.variables as variables
import Config.config as config
from Calculus.Initialisation.LoadingInCache import GeocodeInsee
from Calculus.Initialisation.LoadingInCache import CountiesIndexes
from Data.DB.Mongo.mongo import Mongo
from Data.Hypervisor.Politics.RamDBCalculusPolitic import RamDBCalculusPolitic
from Global.Global import GlobalREFiltered
import numpy as np


class LoadinginCacheTest(unittest.TestCase):

    def setUp(self):
        print('\n [NEW TEST] -- %s \n' % self._testMethodName)
        kwargs = {'DB-opt': {'database': "RamDBPoliticGlobalTest", 'collection': "default"}}
        variables.cache = RamDBCalculusPolitic(**kwargs)
        kwargs_mongo = {'database': config.MONGODB_METEOR_DATABASE, 'collection': config.__GEOCODES_COLLECTIONS__[0]}
        variables.mongo = Mongo(**kwargs_mongo)
        variables.calculs = GlobalREFiltered(alias=config.CALCULUS_ALIAS, filters=config.CALCULUS_MODULES)

    def tearDown(self):
        temp = variables.cache._RamDBCalculusPolitic__cache_ramdb
        temp._RamDBPolitic__cache_db._client.drop_database("RamDBPoliticGlobalTest")
        variables.cache = None
        variables.mongo = None
        variables.calculs = None

    def test_GeocodeInsee(self):
        a = GeocodeInsee()
        ageo = a._run()
        geocodes = variables.cache.get_val('geocodes')
        geocodes_index = variables.cache.get_val('geocodes_index')
        self.assertEqual(ageo, None)
        self.assertEqual(len(geocodes), 36253)
        rdm_geo = random.choice(list(geocodes_index.keys()))
        self.assertEqual(geocodes[geocodes_index[rdm_geo]], rdm_geo)
        temp = variables.cache._RamDBCalculusPolitic__cache_ramdb._RamDBPolitic__cache_ram._cache_dict
        self.assertEqual(set(temp.keys()), {'geocodes_index', 'geocodes'})

    def test_CountiesIndexes(self):
        a = CountiesIndexes()
        counties = a._run()
        geo_method = "Calculus.Initialisation.LoadingInCache.GeocodeInsee"
        geocodes = variables.cache.get_val('geocodes', method=geo_method)
        rdm_county = random.choice(list(counties.keys()))
        while rdm_county == 'FR99999':
            rdm_county = random.choice(list(counties.keys()))
        start_idx = counties[rdm_county]['start']
        self.assertEqual(geocodes[start_idx][2:4], rdm_county[5:7])
        self.assertTrue(int(geocodes[max(start_idx - 1, 0)][2:4]) <= int(geocodes[start_idx][2:4]))
        self.assertEqual(counties['FR99999'], {'start': 0, 'end': 36252})
