
import hashlib
import pickle
import time
import random

from Config.config import __HASH__
import Config.config as config
import Config.variables as variables
from Data.data import Data
from Calculus.CalcVar import CalcVar

from Calculus.exceptions import CalculusError, CalculusPostponed, CalculusDepend, FunctionCalcNeeded

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


# TODO: init => exclude_var_from_hash
class Calculus(object):
    '''	Calculus class. '''

    def __init__(self, *args, **kwargs):
        '''	Initialization function. '''
        super().__init__()
        if __debug__:
            logger.debug('args = %s, kwargs = %s', args, kwargs)
        self._meteor = kwargs.get('meteor', None)
        self._simu_id = kwargs.get('simulation_id', None)
        self._subscription = kwargs.get('subscription', None)

        # Should return a always new name when calculus run
        self._always_new = kwargs.get('always_new', False)
        if self._meteor is not None:
            self._cache = self._meteor._cache
        else:
            self._cache = variables.cache

        # Should I raise or wait dependencies (only for checking deps in init)
        self._raise_if_depends = kwargs.get('raise_if_depends', False)
        # Add depends = [ varHash1, varHash2, ...] if calculus depends on
        # variables in cache
        self._depends = kwargs.get('depends', [])
        self._depend_vars = {}
        # Should we check the cache for variables values in calculus?
        self._skip_cache = kwargs.get('skip_cache', True)
        # force the return variable name
        self._forced_name = kwargs.get('forced_name', None)
        # Should we compute hash variable name
        self._skip_hash = kwargs.get('skip_hash', False)
        # Should the hash be only computed from the module and simu_id
        self._simu_specific = kwargs.get('simu_specific')
        # Save value calculated after run
        self._save_calculation = kwargs.get('save_calculation', False)
        # Save value calculated after run only localy
        self._save_local = kwargs.get('save_local', False)
        if self._simu_specific is not None:
            self._skip_hash = False
            self._skip_cache = False
            self._save_calculation = True
            self._save_local = True

        # should we consume jobs in order to wait all variables values
        self._consume_jobs = kwargs.get('consume_jobs', False)
        # Should dependencies be recursivly checked:
        self._depds_recurse = kwargs.get('depds_recurse', False)
        # Compute module name.
        # We have module name in kwargs
        # We keep the reel name of the module
        # Not the alias-resolved one
        self._module = kwargs.get('module', '%s.%s' % (self.__module__, self.__class__.__name__))

    def calculus(self, module, *args, skip_wrapper=False, **kwargs):
        if skip_wrapper:
            loader = variables.jobs_calculs
        else:
            loader = variables.calculs
        return loader.get_instance(module, *args, meteor=self._meteor, consume_jobs=self._consume_jobs,
                                   simulation_id=self._simu_id, subscription=self._subscription, **kwargs)

    def progress(self, percent=-1, message="", add_percent=-1, time_left=-1, sub_time_left=-1):
        if __debug__:
            logger.debug('progress : %s/%s (%s/%s) => %s', time_left, percent, sub_time_left, add_percent, message)
        if self._simu_id is None or self._meteor is None:
            return None
        send_progress = getattr(self._meteor, 'send_progress', None)
        if callable(send_progress):
            send_progress(self._simu_id, int(time_left), int(sub_time_left),
                          float(percent), float(add_percent), message)
        return None

    def _dependance_waiting(self, var, force_consume=False, keep_calcvar=False):
        if not (self._consume_jobs or force_consume) or self._meteor is None or self._raise_if_depends:
            if __debug__:
                logger.debug('Should I raise : %s, Could consume: %s, with my master %s',
                             self._raise_if_depends, self._consume_jobs, self._meteor)
            raise CalculusPostponed()
        # OK we have the GO order to consume another jobs
        if __debug__:
            logger.debug('Consuming just one request to wait for %s', var.name)
        while True:
            if self._meteor._should_stop:
                raise Exception("Should Stop")
            try:
                curjob = self._meteor._current_job
                consumed = self._meteor.consume_one(timeout=config.DEFAULT_REDIS_TIME)
                self._meteor._current_job = curjob
                if __debug__:
                    if not consumed:
                        logger.debug('Waiting %s var name, No message consumed or bad handling in one of them.',
                                     var.name)
                time.sleep(config.sleep_time_for_dependencies)
                value = self.get_variable(var, keep_calcvar=keep_calcvar)
                return value
            except (CalculusDepend, CalculusPostponed):
                continue
            except CalculusError:
                # TODO trait CalculusError
                if __debug__:
                    logger.critical('CalculusError when waiting %s', var.name)
                raise

    # Check dependance and return value of dependances
    def _check_dependances(self, args, kwargs, with_depends=True, recursif_check=False):
        ret_args = []
        ret_kwargs = {}
        if with_depends and self._depends is not None:
            for depend in self._depends:
                if __debug__:
                    logger.debug('[%s] Dependency : %s', self._hash, depend)
                while True:
                    if self._meteor._should_stop:
                        raise Exception("SHould Stop")
                    try:
                        argsFun = (None, None)
                        fun = None
                        if isinstance(depend, tuple):
                            # We have function / args in dependance variable : Extract it
                            if len(t) >= 3:
                                if isinstance(t[2], tuple) and len(t[2]) == 2 and \
                                   isinstance(t[2][0], list) and isinstance(t[2][1], dict):
                                    argsFun = t[2]
                                else:
                                    argsFun = ([t[2]], None)
                            if len(t) >= 2:
                                fun = t[1]
                            if len(t) >= 1:
                                depend = t[0]
                        var = None
                        if isinstance(depend, CalcVar):
                            var = depend
                        else:
                            var = CalcVar(depend, None, 'CalculusDepend:Var In Dependencies',
                                          function=fun, argsFun=argsFun)
                        self._depend_vars[depend] = self.get_variable(var, self._depend_vars)
                        # Check if all CalcVar inside are OK
                        if recursif_check:
                            self.recursif_depds(var)
                        break
                    except (CalculusDepend, CalculusPostponed):
                        # Wait for dependance (or not depending of the config)
                        self._depend_vars[depend] = self._dependance_waiting(var)

        # argument should be present!
        for arg in args:
            if __debug__:
                logger.debug(' Arg : %s', arg)
            try:
                val = self.get_variable(arg, self._depend_vars)
                ret_args.append(val)
                if recursif_check:
                    self.recursif_depds(val)
            except (CalculusDepend, CalculusPostponed):
                # Wait for dependance (or not depending of the config)
                ret_args.append(self._dependance_waiting(arg))

        for key, arg in kwargs.items():
            if __debug__:
                logger.debug(' Kwarg : %s => %s', key, arg)
            try:
                val = self.get_variable(arg, self._depend_vars)
                ret_kwargs[key] = val
                if recursif_check:
                    self.recursif_depds(val)

            except (CalculusDepend, CalculusPostponed):
                # Wait for dependance (or not depending of the config)
                ret_kwargs[key] = self._dependance_waiting(arg)

        # Now every variable should have a value!
        return (ret_args, ret_kwargs)

    def get_variable(self, var, dependencies={}, wait_var=False, keep_calcvar=False):
        try:
            try:
                return self._variable(var, dependencies, keep_calcvar)
            except FunctionCalcNeeded as e:
                # We have no value but we could try to calculate it!
                if __debug__:
                    logger.error('Trying calculation of variable %s', var.name)
                return e.tryCalculation(self)
        except CalculusError:
            if __debug__:
                logger.error('Trying to recover a variable which is in ERROR state')
            raise
        except (CalculusPostponed, CalculusDepend):
            if __debug__:
                logger.debug('Trying to recover a variable which is in Postponed state')
            if wait_var:
                try:
                    return self._dependance_waiting(var, force_consume=True, keep_calcvar=keep_calcvar)
                except CalculusPostponed:
                    raise CalculusDepend(var.name)
            raise CalculusDepend(var.name)

    def _variable(self, var, dependencies={}, keep_calcvar=False):
        # Get real value of variable
        if not isinstance(var, CalcVar):
            # OK, not our complexe variable type
            # Should be a value, return it
            return var

        # Our complexe variable
        if var.status == 'OK':
            # Value is OK, return it
            if keep_calcvar:
                return var
            else:
                return var._get_value(self._cache)

        if var.name is not None:
            # OK, var name here, recover status from cache or dependencies
            if var.name in dependencies:
                var._set_value(dependencies[var.name], self._cache)
                if keep_calcvar:
                    return var
                else:
                    return var._get_value(self._cache)
        # Recover value or throw exception
        val = var._get_value(self._cache)
        # No exception : value is OK
        if keep_calcvar:
            return var
        else:
            return val

    # Execute the calculus if we can
    def _execute(self, varName, args, kwargs):
        try:
            if __debug__:
                logger.debug('Checking Dependances')
            (args, kwargs) = self._check_dependances(args, kwargs, recursif_check=self._depds_recurse)
            if __debug__:
                logger.debug('Running calculation %s', self._module)
            # Do not raise inside calculus
            self._raise_if_depends = False
            value = self._run(*args, **kwargs)
            if __debug__:
                logger.debug('Calculation %s has run', self._aliased_class)
            # We have a value or a complexe variable.
        except CalculusError as e:
            if __debug__:
                logger.error('Calculation error (%s) in %s.%s with arg: args=%s kwargs=%s',
                             e, self.__module__, self.__class__.__name__, args, kwargs)
            # TODO: Post in redis queue simulation failed?
            # TODO:  + aws_launcher should intercept message and kill all jobs for this simulation
            e.varname = varName
            raise e
        except CalculusPostponed as e:
            if __debug__:
                logger.info('Calculation postponed (%s) in %s.%s with arg: args=%s kwargs=%s',
                            e, self.__module__, self.__class__.__name__, args, kwargs)
            e.varname = varName
            raise e
        if isinstance(value, CalcVar):
            # update varname
            value._set_name(varName, cache=self._cache)
            return value
        elif value is not None:
            # Value is OK, return a CalcVar
            return CalcVar(varName, value, 'OK')

        # ret value is None, return None
        return None

    # Run the calculus
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        varName = self._forced_name
        value = None
        status = None
        if self._meteor is not None:
            self._meteor._current_job['type'].append('Calculus(%s)' % (self._aliased_class))
        if not self._skip_hash or (not self._skip_cache and varName is None):
            # Calc hash corresponding to the variable name
            varName = self._calc_hash(args, kwargs)
        self._hash = varName
        if self._skip_cache:
            # We skip the cache check of value
            # We didn't need the varName hash since we want values
            # IF NOT CHANGE THIS
            if __debug__:
                logger.debug('Skipping cache checking')
            ret = self._execute(varName, args, kwargs)
            if self._save_calculation:
                ret.sync_cache(self._cache, local=self._save_local)
            if self._meteor is not None:
                self._meteor._current_job['type'].pop()
            return ret
        try:
            value = self._cache.get_val(varName)
            status = self._cache.get_val('%s:status' % (varName))
            if __debug__:
                logger.debug('Found variables %s : value %s , status %s', varName, value, status)
            # Check status against Postponed calculus
        except KeyError as e:
            status = 'FAILED:KeyError'
            if __debug__:
                logger.debug('Calculus Variable Not Found %s : %s' % (varName, e))

        if status != 'OK':
            ret = self._execute(varName, args, kwargs)
            # TODO ERROR: ret could be None
            if ret.name is not None and self._save_calculation:
                self._cache.set_val(ret.name, Calculus.flatten_calcvar(ret._get_value(self._cache)),
                                    local=self._save_local)
                self._cache.set_val('%s:status' % (ret.name), ret.status, local=self._save_local)
        else:
            ret = CalcVar(varName, value, status, True)
        if self._meteor is not None:
            self._meteor._current_job['type'].pop()
        return ret

    def recursif_depds(self, value):
        # Save (list|dist)* of CalcVar
        if __debug__:
            logger.debug("Recursif checking of %s", value)
        if isinstance(value, dict):
            for val in value.values():
                self.recursif_depds(val)
        elif isinstance(value, list):
            for val in value:
                self.recursif_depds(val)
        elif isinstance(value, CalcVar):
            val = None
            try:
                val = value._get_value(self._cache)
            except (CalculusDepend, CalculusPostponed):
                # Wait for dependance (or not depending of the config)
                val = self._dependance_waiting(value)
            self.recursif_depds(val)

    @staticmethod
    def flatten_calcvar(value, save=True):
        # Save (list|dist)* of CalcVar
        if isinstance(value, dict):
            return {key: Calculus.flatten_calcvar(val) for key, val in value.items()}
        elif isinstance(value, list):
            return [Calculus.flatten_calcvar(val) for val in value]
        elif isinstance(value, CalcVar):
            if save and value._dirty:
                value.sync_cache(self._cache)
            return value.name
        else:
            return value

    @staticmethod
    def calculus_to_hash(calculation, args, kwargs):
        if __debug__:
            logger.debug('Calculate hash for calculus')
        h = hashlib.new(__HASH__)
        h.update(bytes(calculation, 'utf-8'))
        for arg in args:
            if isinstance(arg, CalcVar):
                # Meta variable!
                if config.hash_prefers_value and arg._get_value(variables.cache) is not None:
                    arg = pickle.dumps(arg._get_value(variables.cache))
                else:
                    arg = bytes(arg.name, 'utf-8')
            else:
                arg = bytes(CalcVar.to_name(arg), 'utf-8')
            h.update(arg)
        for var, arg in kwargs.items():
            h.update(bytes(var, 'utf-8'))
            if isinstance(arg, CalcVar):
                # Meta variable!
                if config.hash_prefers_value and arg._get_value(variables.cache) is not None:
                    arg = pickle.dumps(arg._get_value(variables.cache))
                else:
                    arg = bytes(arg.name, 'utf-8')
            else:
                arg = bytes(CalcVar.to_name(arg), 'utf-8')
            h.update(arg)
        return h.hexdigest()

    @staticmethod
    def _static_calc_hash(simu_specific, always_new, module, simu_id, args, kwargs):
        if always_new:
            return '%X' % random.getrandbits(256)
        if simu_specific is not None:
            if type(simu_specific) is bool:
                if simu_specific:
                    return Calculus.calculus_to_hash(module, [simu_id], {})
            elif type(simu_specific) is list:
                return Calculus.calculus_to_hash(module, [simu_id] + simu_specific, {})
            else:
                return 'SS-%X' % random.getrandbits(256)
        if config.no_hash_for_calculus:
            return '%X' % random.getrandbits(256)
        else:
            return Calculus.calculus_to_hash(module, args, kwargs)

    def _calc_hash(self, args, kwargs):
        return Calculus._static_calc_hash(self._simu_specific, self._always_new,
                                          self._module, self._simu_id,
                                          args, kwargs)

    def _run(self, *args, **kwargs):
        ''' Stub function to run the main calcul '''
        raise NotImplementedError()


class Dummy(Calculus):

    def _run(self, *args, **kwargs):
        if __debug__:
            logger.error('Running Dummy Calculus')
        return None
