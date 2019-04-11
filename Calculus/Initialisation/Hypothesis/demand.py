import numpy as np

import pymongo

import Config.variables as variables
import Config.config as config
import babel.dot.initial_values as defcomp
from Calculus.calculus import Calculus

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class AnimalsNumber(Calculus):

    def _run(self, **kwargs):
        distrib_ini = self._cache.get_val('agri_animals_abs')
        return np.array(distrib_ini)


class PlantsSurface(Calculus):

    def _run(self, **kwargs):
        distrib_ini = self._cache.get_val('agri_surf_abs')
        return np.array(distrib_ini)


class EmployeesInd(Calculus):

    def _run(self, **kwargs):
        varidx = defcomp.IND_DICT_REV[kwargs.get('varname').split('_')[0]]
        employees_ini = self._cache.get_val('Demand:Industry:Employees:Ini')
        return employees_ini[:, varidx]


class Ntrain(Calculus):

    def _run(self, **kwargs):
        return self._cache.get_val('n_train_station')


class Nairport(Calculus):

    def _run(self, **kwargs):
        return self._cache.get_val('n_airport')


class Nparking(Calculus):

    def _run(self, **kwargs):
        return self._cache.get_val('n_parking')


class KMroad(Calculus):

    def _run(self, **kwargs):
        return self._cache.get_val('km_road')


class KMhighway(Calculus):

    def _run(self, **kwargs):
        return self._cache.get_val('km_highway')


class Nbikeroad(Calculus):

    def _run(self, **kwargs):
        geocodes = self._cache.get_val('geocodes')
        return np.zeros((len(geocodes),))
