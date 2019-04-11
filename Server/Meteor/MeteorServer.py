
from redis import StrictRedis
import ast

import Config.config as config
import Config.variables as variables

from Server.server import Server
from babel.queue import RedisPriorityQueue, Consumer
from babel.messages import LAUNCH_SIMULATION, JOBS

from Calculus.exceptions import CalculusError, CalculusPostponed

from Global.Global import GlobalFiltered, ModuleNotAuthorized, ClassNotAuthorized


if __debug__:
    import logging
    logger = logging.getLogger(__name__)
else:
    from Utils.progress_bar import printProgress


class MeteorServer(Server, Consumer):

    def __init__(self, *args, timed_simu=False, cache=None, cache_conf=config.CACHE_CONF,
                 redis=None, start_redis=False, conf_redis=config.REDIS_CONF,
                 queue=None, start_queue=False, conf_queue=config.REDIS_QUEUE_CONF,
                 **kwargs):
        """	Initialization class. """
        # Initialise Server Parent
        super().__init__(**kwargs)
        if __debug__:
            logger.debug("Initialization...")
        # Counter of jobID watchdog
        self._jobs_id_wd = {}
        self._current_job = None

        # = Initialise the Queue
        def_queue = ['MeteorServer.urgent', 'MeteorServer.%s.%x' % (self._instance_name, self._id_thread),
                     'MeteorServer.%s' % (self._instance_name)]
        if isinstance(conf_queue['queue_name'], list):
            def_queue.extend(conf_queue['queue_name'])
        elif isinstance(conf_queue['queue_name'], str):
            def_queue.append(conf_queue['queue_name'])
        # == Queue param present : use it
        if queue is None:
            # No redis present => start a new Queue
            # = Initialise the Redis
            # == Redis param present : use it
            if redis is None:
                # No redis present => start a new Redis Client
                if start_redis or variables.redis is None:
                    # == Start a new Redis Client
                    redis = StrictRedis(**conf_redis)
                else:
                    # == Get default redis client with args passed to the MeteorServer
                    redis = variables.redis
            if start_queue or variables.queue is None:
                # == Start a new Queue Client
                queue = RedisPriorityQueue(def_queue, redis)
            else:
                # == Get default redis queue with args passed to the MeteorServer
                queue = variables.queue
        # Set consumer queue
        self._Consumer__queue = queue

        # Get the cache for the Meteor Server
        if cache is None:
            # No cache given => get cache from global var
            cache = variables.cache
        elif isinstance(cache, str):
            # Get instance of cache with string
            cache = variables.loader.get_instance(cache, **cache_conf)
        if cache is None:
            raise ValueError("cache inside MeteorServer should not be None")
        self._cache = cache

        self._timed_simu = timed_simu
        # Instanciate a dynamic Jobs Loader
        self._jobs_loader = GlobalFiltered(alias=config.JOBS_ALIAS, filters=config.JOBS_IMPLEMENTED)

        self.current_request = None
        if __debug__:
            logger.debug("Initialisation of MeteorServer done: Waiting orders on queue %s", def_queue)

    def launch(self):
        """
        Launch infinite loop and check if redis simulation db have waiting simulations.
        """
        if __debug__:
            logger.debug("Launch the consume")
        # We have handler so we need to timeout on read operation in REDIS
        # Jobs could run jobs inside to wait for dependencies
        self._consume(opt_handle={'consume_jobs': True}, timeout=config.DEFAULT_REDIS_TIME)

    def handle_message(self, message, opt_handle=None, queue=None):
        self._current_job = {'type': [None], 'id': None}
        if __debug__:
            logger.info("Launch request : {0}".format(message))
        self.current_request = message
        event = message['event']
        if event == JOBS:
            act = self._run_jobs
        elif event == LAUNCH_SIMULATION:
            act = self._run_simulation
        else:
            if __debug__:
                logger.error("Unknown event '%s'", event)
            self.current_request = None
            return False

        # if self._timed_simu:
        #     with Timer() as tm1:
        #         ret = act(message, opt_handle=opt_handle, timed=tm1)
        # else:
        ret = act(message, opt_handle=opt_handle)
        self.current_request = None
        self._current_job = None
        return ret

    def _run_calculus(self, request, args, timed=None):
        self._current_job['type'][0] = 'Calculus(%s)' % (request["module"])
        calc = self._jobs_loader.get_instance(request["module"],
                                              *args["init_args"],
                                              module=request["module"],
                                              **args["init_kwargs"])

        return calc.run(*args["run_args"], **args["run_kwargs"])

    def _run_jobs(self, request, opt_handle=None, timed=None):
        if __debug__:
            logger.debug("Launching Jobs")
        job_id = request['job.id']

        self._current_job = {'id': job_id, 'type': ['Job']}
        args = {
            "init_args": [],
            "init_kwargs": {},
            "run_args": [],
            "run_kwargs": {}
        }

        # Get options
        for option in ["init_args", "init_kwargs", "run_args", "run_kwargs"]:
            if option in request:
                try:
                    args[option] = ast.literal_eval(request[option])
                except Exception as e:
                    if __debug__:
                        logger.error("Get exception when converting %s in python literal : %s", option, str(e))

        # basic check of type
        if not isinstance(args["init_kwargs"], dict):
            if __debug__:
                logger.error("init_kwargs not a dict")
            return False
        elif not isinstance(args["run_kwargs"], dict):
            if __debug__:
                logger.error("run_kwargs not a dict")
            return False
        elif not isinstance(args["init_args"], list):
            if __debug__:
                logger.error("init_args not a list")
            return False
        elif not isinstance(args["run_args"], list):
            if __debug__:
                logger.error("run_args not a list")
            return False

        self._jobs_id_wd[job_id] = self._jobs_id_wd.get(job_id, 0) + 1

        if self.job_watchdog(request, args):
            return False

        if request["type"] == "calculus":
            try:
                if opt_handle is not None:
                    # This calculus should not run jobs inside ?
                    args["init_kwargs"]["consume_jobs"] = opt_handle.get("consume_jobs", False)
                # Add meteor reference to get cache & co
                args["init_kwargs"]["meteor"] = self
                retcal = self._run_calculus(request, args, timed=timed)
            except ModuleNotAuthorized as e:
                if __debug__:
                    logger.error("Try to load an unauthorized module '%s' : %s", request["module"], e)
                return False
            except ClassNotAuthorized as e:
                if __debug__:
                    logger.error("Try to load an unauthorized class '%s' : %s", request["module"], e)
                return False
            except ImportError as e:
                if __debug__:
                    logger.error("Error importing class '%s' : %s", request["module"], e)
                return False
            # Calculus Error now
            except CalculusError:
                if __debug__:
                    logger.error("Error in doing Calculus")
                return False
            except CalculusPostponed as e:
                return True
        else:
            return False

        if __debug__:
            logger.debug("Jobs returns '%s'", retcal)
        return True

    def _run_simulation(self, request, opt_handle=None, timed=None):
        if opt_handle is None:
            opt_handle = {}

        self._current_job = {'type': ['Simulation'], 'id': request['simulation_id']}
        if request['simu_type'] == "eval":
            if __debug__:
                logger.debug("Launching new Evaluation")
            evalSimu = variables.calculs.get_instance(
                "Evaluation", consume_jobs=opt_handle.get("consume_jobs", False), meteor=self)
            return evalSimu(request)
        elif request['simu_type'] == "eod":
            if __debug__:
                logger.debug("Launching new EOD")
            evalSimu = variables.calculs.get_instance(
                "EOD", consume_jobs=opt_handle.get("consume_jobs", False), meteor=self)
            return evalSimu(request)
        else:
            if __debug__:
                logger.debug("Launching new Simulation")
            simu = variables.calculs.get_instance(
                "Simulation", consume_jobs=opt_handle.get("consume_jobs", False), meteor=self)
            with variables.lockPercentSimu:
                variables.percentSimu[request['simulation_id']] = {
                    'cur': 0,
                    'max': request.get('percent', 100),
                }
            MeteorServer.send_progress(self, request['simulation_id'], -1, -1, 0, -1, msg="Receiving simulation")
            return simu(request)

    def job_watchdog(self, request, args):
        # Condition for a job to be "OK, don't worry about me"
        if self._jobs_id_wd[request['job.id']] < config.MAX_JOB_RESENT:
            return False

        # Oh wait, I should worry about this job!
        if __debug__:
            logger.warning("Job ID %s reach max number (%d), %s",
                           request['job.id'], self._jobs_id_wd[request['job.id']],
                           MeteorServer._display_job_info(request, args))

        # for now, we always run jobs so return False
        return False

    @staticmethod
    def _display_job_info(request, args):
        # For now display only jobs name/time
        ret_str = request['module']
        if 'forced_method' in args['init_kwargs']:
            ret_str = args['init_kwargs']['forced_method']
        ret_str = "%s(%s)" % ("ret_str", request['time.created'])

        if 'simulation_id' in args['init_kwargs']:
            ret_str = "%s(%s)" % ("ret_str", args['init_kwargs']['simulation_id'])

        return ret_str

    def send_progress(self, simu_id, time_left, sub_time_left, percent, add_percent, msg):
        percentS = None
        with variables.lockPercentSimu:
            percentS = variables.percentSimu.get(simu_id, {'cur': 0, 'max': 100})
            if percent > 0:
                percentS['cur'] = percent
            elif add_percent > 0:
                percentS['cur'] += add_percent

            variables.percentSimu[simu_id] = percentS

        if __debug__:
            logger.info("Percent for simu %s : %s - %s", simu_id, percentS, msg)
        else:
            printProgress(percentS['cur'], percentS['max'], prefix='Progress of %s:' % (simu_id),
                          suffix='Complete', barLength=50, lock=True)

    def send_done(self, simu_id):
        with variables.lockPercentSimu:
            del variables.percentSimu[simu_id]
        if __debug__:
            logger.debug("Percent for simu %s : 100%% :=> DONE", simu_id)
        else:
            printProgress(100, 100, prefix='Progress of %s:' % (simu_id), end=True,
                          suffix='Complete(DONE)', barLength=50, lock=True)
