import datetime
import pickle
import random

from Calculus.calculus import Calculus
import Config.variables as variables
import Config.config as config

from Calculus.CalcVar import CalcVar
from Calculus.exceptions import CalculusError, CalculusPostponed, CalculusDepend

from babel.messages import JOBS

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


# Exception for Calculus handle in MeteorServer ?
class CalculJob(Calculus):

    def __init__(self, *args, **kwargs):
        # Try to unpickle arguments for now
        (args, kwargs) = CalculJob._convert_from_name(args, kwargs)
        super().__init__(*args, **kwargs)

        # We didn't want this module name, but the target module calculus.
        # Not present => dummy calculus
        self._module = kwargs.get("method", "Calculus.calculus.Dummy")
        # Module but loaded another class? (bypass aliases by setting the module name)
        self._force_loaded_module = kwargs.get("forced_method", None)
        # By defautl, save the resut to cache!
        self._save = kwargs.get("save_calculus", False)
        # Getting varName
        self._varname = kwargs.get("varname", None)
        self._kwargs = kwargs
        self._args = args

    @staticmethod
    def _convert_from_name(args, kwargs):
        # Convert from hash_name to CalcVar
        ret_args = []
        ret_kwargs = {}
        for arg in args:
            if isinstance(arg, bytes):
                # try pickled data
                try:
                    ret_args.append(pickle.loads(arg))
                except pickle.UnpicklingError:
                    ret_args.append(arg)
            elif not isinstance(arg, str):
                ret_args.append(arg)
            elif config.__HASH_RE__.match(arg):
                ret_args.append(CalcVar(arg, None, "CalculusPostponed:"))
            else:
                ret_args.append(arg)

        for key, arg in kwargs.items():
            if isinstance(arg, bytes):
                # try pickled data
                try:
                    ret_kwargs[key] = pickle.loads(arg)
                except pickle.UnpicklingError:
                    ret_kwargs[key] = arg
            elif not isinstance(arg, str):
                ret_kwargs[key] = arg
            elif config.__HASH_RE__.match(arg):
                ret_kwargs[key] = CalcVar(arg, None, "CalculusPostponed:")
            else:
                ret_kwargs[key] = arg

        return (ret_args, ret_kwargs)

    def run(self, *args, **kwargs):
        try:
            if self._force_loaded_module is not None:
                calc = variables.jobs_calculs.get_instance(self._force_loaded_module, *self._args, **self._kwargs)
            else:
                calc = variables.jobs_calculs.get_instance(self._module, *self._args, **self._kwargs)

            if __debug__:
                logger.info("Running Calculus %s (save in cache : %s)", self._module, self._save)
                logger.debug("Running Calculus Forced Name : %s", self._kwargs.get("forced_name", "(none)"))

            (args, kwargs) = CalculJob._convert_from_name(args, kwargs)

            val = calc(*args, **kwargs)
            #TODO ERROR : could be none.
            if __debug__:
                logger.info("Return value is: %s", val)
            if self._varname is not None and val.name != self._varname:
                if __debug__:
                    logger.debug("Calculated hash from calculus differ from asked varname")
                varName = self._varname
                cached = False
            else:
                varName = val.name
                cached = val.cached
            if varName is None:
                return val._get_value(self._cache)

            if val.status == "OK":
                if cached:
                    if __debug__:
                        logger.debug("Value is cached => not saving")
                    pass
                elif self._save:
                    self._cache.set_val(varName, val._get_value(self._cache))
                else:
                    if __debug__:
                        logger.warning("Value %s not cached even though OK, check self._save status." +
                                       "Setting to True anyway", varName)
                    self._cache.set_val(varName, True)
            else:
                if __debug__:
                    logger.error("ERROR without exception: %s", val.status)
                pass
            if not cached:
                self._cache.set_val("%s:status" % (varName), val.status)

            if __debug__:
                if "forced_name" in self._kwargs and varName != self._kwargs.get("forced_name", "(none)"):
                    logger.debug("VarName (%s) != ForcedName(%s)", varName, self._kwargs.get("forced_name", "(none)"))

            return val._get_value(self._cache)
        except CalculusError as e:
            if __debug__:
                logger.warning("ERROR in doing calculus %s for asked var %s", self._module, self._varname)
            varName = self._varname
            if varName is None:
                varName = calc._hash
            if varName is not None:
                self._cache.set_val(varName, None)
                self._cache.set_val("%s:status" % (varName), str(e))
            raise
        except CalculusPostponed as e:
            if __debug__:
                logger.info("POSTPONED calculus %s for asked var %s", self._module, self._varname)
            varName = self._varname
            if varName is None:
                varName = calc._hash
            if varName is not None:
                self._cache.set_val(varName, None)
                self._cache.set_val("%s:status" % (varName), str(e))
            raise
        raise CalculusError("Return not correct")


# Exception for Calculus handle in MeteorServer ?
class WrapperJob(Calculus):
    """
    Wrap a calculus inside a Job
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Module to call for running Calculus Job
        self._module = "Calculus.Job.CalculJob"

        self._kwargs = kwargs
        self._args = list(args)

        if self._meteor is None:
            if __debug__:
                logger.error("Could not wrap calculus %s in job if meteor is None", self._module)
            raise ValueError("Meteor should not be None")

    def _convert_to_name(self, args, kwargs, pickle_all=False):
        # Convert from CalcVar or Value to hash name
        # And save it into cache
        # exception if type is str, int, float or datetime
        ret_args = []
        ret_kwargs = {}
        type_serialize_arg = (str, int, float, datetime.datetime)
        for arg in args:
            if pickle_all or isinstance(arg, type_serialize_arg):
                ret_args.append(pickle.dumps(arg))
            elif isinstance(arg, CalcVar) and arg.serialize:
                ret_args.append(pickle.dumps(arg._get_value(self._cache)))
            else:
                if not isinstance(arg, CalcVar):
                    arg = CalcVar(None, arg, "OK")
                varName = arg.name
                # TODO: correction @variables.cache
                if not self._cache.in_cache(varName):
                    self._cache.set_val(varName, arg._get_value(self._cache))
                    self._cache.set_val("%s:status" % (varName), arg.status)
                ret_args.append(varName)

        for key, arg in kwargs.items():
            if pickle_all or isinstance(arg, type_serialize_arg):
                ret_kwargs[key] = pickle.dumps(arg)
            elif isinstance(arg, CalcVar) and arg.serialize:
                ret_kwargs[key] = pickle.dumps(arg._get_value(self._cache))
            else:
                if not isinstance(arg, CalcVar):
                    arg = CalcVar(None, arg, "OK")
                varName = arg.name
                if not self._cache.in_cache(varName):
                    self._cache.set_val(varName, arg._get_value(self._cache))
                    self._cache.set_val("%s:status" % (varName), arg.status)
                ret_kwargs[key] = varName

        return (ret_args, ret_kwargs)

    def run(self, *args, **kwargs):
        # Emit the job and return CalcVar
        # Get the reel calculus
        self._kwargs["method"] = self._aliased_class
        try:
            # Try to delete kwargs value depending of this thread
            del self._kwargs["meteor"]
        except KeyError:
            # Don't care if we delete key not in dict
            pass
        try:
            # Consume job set by MeteorServer
            del self._kwargs["consume_jobs"]
        except KeyError:
            # Don't care if we delete key not in dict
            pass
        (nargs, nkwargs) = self._convert_to_name(args, kwargs)
        # Calculing hash the same way that Calculus without WrapperJob do
        varName = Calculus._static_calc_hash(self._kwargs.get("simu_specific", False),
                                             self._kwargs.get("always_new", False),
                                             self._aliased_class, self._simu_id,
                                             args, kwargs)
        self._kwargs["varname"] = varName
        (nargs_init, nkwargs_init) = self._convert_to_name(self._args, self._kwargs, pickle_all=True)
        message = {
            'event': JOBS,
            'type': 'calculus',
            'module': self._module,
            'init_args': "%s" % (nargs_init),
            'init_kwargs': "%s" % (nkwargs_init),
            'run_args': "%s" % (nargs),
            'run_kwargs': "%s" % (nkwargs),
            'time.created': datetime.datetime.now(datetime.timezone.utc).timestamp(),
            'job.id': '%X' % random.getrandbits(256)
        }
        if __debug__:
            logger.info("Emiting  Calculus %s", self._aliased_class)
        self._meteor.send_postponed(message)
        return CalcVar(varName, None, "CalculusPostponed:")


# Exception for Calculus handle in MeteorServer ?
class DependsJob(Calculus):
    """
    Wrap a calculus inside a Job
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._kwargs = kwargs
        self._args = list(args)

    def run(self, *args, **kwargs):
        # Try the job and return a wrapped job if jobs failed with Postponed : raise exception to catch here!
        calculation = variables.jobs_calculs.get_instance(self._aliased_class, *self._args,
                                                          raise_if_depends=True, **self._kwargs)

        try:
            return calculation(*args, **kwargs)
        except (CalculusPostponed, CalculusDepend):
            # Wrapp it in WrapperJob
            wrapper = WrapperJob(*self._args, **self._kwargs)
            wrapper._aliased_class = self._aliased_class
            return wrapper(*args, **kwargs)


# Run the Job immediatly
class RunJob(Calculus):
    """
    Run the aliased module instead of postponed the Job
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._kwargs = kwargs
        self._args = list(args)

    def run(self, *args, **kwargs):
        # Run the job
        calculation = variables.jobs_calculs.get_instance(self._aliased_class, *self._args, **self._kwargs)
        return calculation(*args, **kwargs)
