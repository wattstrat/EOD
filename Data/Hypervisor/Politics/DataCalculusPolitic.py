

from Data.Hypervisor.hypervisor import Hypervisor

import Config.variables as variables
import Config.config as config


if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DataCalculusPolitic(Hypervisor):

    def __init__(self, Cache, *args, **kwargs):
        """ Initialization function. """
        super().__init__(*args, **kwargs)
        self.__cache = Cache
        self._meteor = kwargs.get('meteor')

    def in_cache(self, varName):
        return self.__cache.in_cache(varName)

    def rename(self, varName, newName):
        self.__cache.rename(varName, newName)

    def get_val(self, varName, *args, **kwargs):
        """
        get function. Set the hypervisor's metadata, then tries to access data in RAM, if absent tries in db,
        if absent : computes from method kwarg
        If in db, puts it in RAM. In case of memory error tries to make space, if still a problem : error.
        """
        depth = kwargs.get("depth", 0)
        if depth > config.MAX_GETVAL_DEPTH:
            if __debug__:
                logger.error('Max depth reach for get_val with variable %s', varName)
            raise KeyError("%s: Max depth reach" % varName)

        val = None
        method = None
        try:
            val = self.__cache.get_val(varName, *args, catch_error=True, **kwargs)
            if __debug__:
                logger.debug('%s => %s', varName, val)
            return val
        except KeyError:
            if __debug__:
                logger.debug('No variable named %s in the child Cache(%s), try to calculate it', varName,
                             self.__cache.__class__.__name__)
            config_method = config.constants_method.get(varName, None)
            method = kwargs.get('method', config_method)
            if method is None:
                if __debug__:
                    if kwargs.get("catch_error", False):
                        # We catch error in higher call, we do not want a logge.error
                        logger.error('No method to calculate variable named %s', varName)
                    pass
                raise
        if __debug__:
            logger.debug("Var '%s' not found in child Cache (%s), try to calculate it with '%s'", varName,
                         self.__cache.__class__.__name__, method)
        # No value in cache RAM & DB
        init_args = kwargs.get("init_args", [])
        init_kwargs = kwargs.get("init_kwargs", {})

        run_args = kwargs.get("run_args", [])
        run_kwargs = kwargs.get("run_kwargs", {})

        try:
            del init_kwargs['meteor']
        except KeyError:
            pass

        inst = variables.calculs.get_instance(method, *init_args, meteor=self._meteor, **init_kwargs)
        val = inst(*run_args, **run_kwargs)

        # TODO: QUID if Calculus is postponed => KeyError...
        if val is None or val.value is None:
            if __debug__:
                logger.debug('Calculus return None but no exception: get val from Data Cache')
            kwargs['depth'] = depth + 1
            return self.get_val(varName, *args, **kwargs)
        self.__cache.set_val(varName, val.value, *args, **kwargs)

        # get_val return a value
        return val.value

    def set_val(self, varName, value, *args, **kwargs):
        # The set_val is not changed because adding Calculus should not
        # change value Calculus
        val = self.__cache.set_val(varName, value, *args, **kwargs)
        return val

    def del_val(self, varName, *args, **kwargs):
        # The delVal is not changed because adding Calculus should not
        # delete value in Calculus
        self.__cache.del_val(varName)

    def clear(self):
        self.__cache.clear()
