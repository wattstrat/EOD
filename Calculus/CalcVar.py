import random
import hashlib
import pickle
import datetime


import Calculus.exceptions as ex
import Config.config as config
import Config.variables as variables

# TODO: get_name => si pas dans le cache, mettre dans le cache? informée le dvp?

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class RenamingError(Exception):
    pass


class CalcVar(object):

    def __init__(self, name=None, value=None, status=None, cached=False,
                 serialize=False, check_value_is_hash=True, poid=0,
                 function=None, argsFun=(None, None),
                 forward_to_cache=False, random_name=False):
        # CalcVar of CalcVar is CalcVar
        if isinstance(value, CalcVar):
            self._set_nested(value)
        else:
            self._name = name
            self._value = value
            if value is not None and status is None:
                # Value is present, and status not given => OK
                self._status = "OK"
            else:
                self._status = status
            self._cached = cached
            self._serialize = serialize
            self._poid = poid
            self._function = function
            self._argsFun = argsFun
            self._dirty = True
            self._fwd = forward_to_cache
            self._random_name = random_name
            if check_value_is_hash and isinstance(value, str) and config.__HASH_RE__.match(value):
                self._name = value
                self._value = None
                self._status = "CalculusPostponed:"

    def _set_nested(self, nested):
        self._name = nested._name
        self._value = nested._value
        self._status = nested._status
        self._cached = nested._cached
        self._serialize = nested._serialize
        self._poid = nested._poid
        self._function = nested._function
        self._argsFun = nested._argsFun
        self._dirty = nested._dirty
        self._fwd = nested._fwd

    def _recover_exception(self):
        if self._status == "OK":
            return

        if self._function is not None:
            # We have an exception but a way to possibly calculate the variable
            raise ex.FunctionCalcNeeded(self._function, self._args)

        if self._status is None:
            raise ex.UnknownError()

        E = self._status.split(":")
        if len(E) == 0:
            raise ex.UnknownError()
        if E[0] == "CalculusError":
            raise ex.CalculusError()
        elif E[0] == "CalculusPostponed":
            raise ex.CalculusPostponed()
        elif E[0] == "CalculusDepend":
            if len(E) > 1:
                raise ex.CalculusDepend(E[1])
            else:
                raise ex.CalculusDepend(None)
        else:
            raise ex.UnknownError()

    @staticmethod
    def _method_hash(value):
        if config.hash_prefers_value:
            return "hash"
        elif config.name_from_hash_value and isinstance(value, (datetime.datetime, int, float)):
            return "hash"
        elif config.name_from_hash_value and isinstance(value, (list, str, set)) and len(value) < 10000:
            return "hash"
        else:
            return "random"

    @staticmethod
    def to_name(value, forceRandom=False):
        if forceRandom:
            method = "random"
        else:
            method = CalcVar._method_hash(value)
        if __debug__:
            logger.debug("Method to name : %s", method)
        if method == "hash":
            h = hashlib.new(config.__HASH__)
            val = pickle.dumps(value)
            h.update(val)
            return h.hexdigest()
        else:
            return '%X' % random.getrandbits(256)

    @property
    def name(self):
        if self._name is None:
            if self._random_name:
                self._name = CalcVar.to_name(self._value, forceRandom=True)
            else:
                self._name = CalcVar.to_name(self._value)
        return self._name

    @name.setter
    def name(self, forced_name):
        return self._set_name(forced_name, cache=variables.cache)

    def _set_name(self, forced_name, cache):
        if self._name is None:
            self._name = forced_name
            return self._name
        elif self._name == forced_name:
            return self._name
        try:
            if not self._dirty:
                # Rename only if we are in sync!
                cache.rename(self._name, forced_name)
        except KeyError as e:
            # raise RenamingError("Could not rename %s as %s", self._name, forced_name)
            # Don't care if missing in cache
            if __debug__:
                logger.debug("RenamingError : Could not rename %s as %s", self._name, forced_name)
        self._name = forced_name

    @property
    def value(self):
        return self._get_value(cache=variables.cache)

    def _get_value(self, cache):
        if self._status == 'OK':
            # Value is OK, return it
            return self._value

        if self._name is not None:
            # OK, var name here, recover status from cache
            try:
                value = cache.get_val('%s' % (self._name))
                try:
                    status = cache.get_val('%s:status' % (self._name))
                except KeyError:
                    # Status not present => defaut to OK
                    status = 'OK'
                self._value = value
                self._status = status
                self._dirty = False
            except KeyError:
                if __debug__:
                    logger.debug('%s is not present in cache', self._name)
                self._value = None
                self._status = 'CalculusPostponed:'

        # Recompose exception
        self._recover_exception()
        # No exception : value is OK
        return self._value

    @value.setter
    def value(self, newValue):
        return self._set_value(newValue, cache=variables.cache)

    def _set_value(self, newValue, cache):
        if isinstance(newValue, CalcVar):
            self._set_nested(newValue)
        else:
            self._dirty = True
            self._value = newValue
            self._status = "OK"
        if self._fwd:
            self.sync_cache(cache)

        return self._value

    def sync_cache(self, cache, *args, **kwargs):
        if not self._dirty:
            return
        cache.set_val(self.name, self.value, *args, **kwargs)
        cache.set_val("%s:status" % (self.name), self._status, *args, **kwargs)
        self._dirty = False

    def __str__(self):
        return "CalcVar({!s} => {!s} ({!s}) | cached: {!s} | dirty: {!s})".format(
            self._name, self._value, self._status, self._cached, self._dirty)

    def __repr__(self):
        return "CalcVar({!s},{!s},{!s},{!s},{!s})".format(
            self._name, self._value, self._status, self._cached, self._dirty)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, newStatus):
        if self._status == newStatus:
            return self._status
        if newStatus == "OK":
            # OK, newStatus is OK => value is important => we are dirty
            self._dirty = True
        else:
            # Set the status to other => clean the link to release memory
            # clear dirty to prevent overwriting the real value possibly in cache
            self._dirty = False
            self._value = None
        self._status = newStatus

    @property
    def serialize(self):
        return self._serialize

    @serialize.setter
    def serialize(self, val):
        self._serialize = val
