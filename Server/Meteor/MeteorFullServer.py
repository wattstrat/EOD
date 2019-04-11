
from redis import Redis
import time
import random

import Config.config as config

from Server.Meteor.MeteorServer import MeteorServer
from babel.queue import RedisPriorityQueue, RedisQueue, Producer
from babel.messages import SIMULATION_ERROR, RESULTS_AVAILABLE, SIMULATION_PROGRESS

from Calculus.exceptions import CalculusError, CalculusPostponed

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


# A Meteor Server that just receive jobs / simu and discard jobs but return multiple message for ProgressSimu
class MeteorFullServer(MeteorServer, Producer):

    def __init__(self, *args, **kwargs):
        """	Initialization class. """
        # Initialise MeteorServer Parent
        super().__init__(**kwargs)

        if __debug__:
            logger.debug("Initialization Full Server : Consume/Produce...")

        # = Initialise the Result Queue
        result_queue = [config.OUTGOING_COMMUNICATION_QUEUE]
        # Steal redis instance from Consumer queue
        self._Producer__queue = RedisQueue(result_queue, self._Consumer__queue._redis)

        # TODO: have specific function to send to specific jobs postponed queue?
        typePostponed = config.OUTGOING_JOBS_POSTPONED_QUEUE_TYPE
        qJobsPostponed = config.OUTGOING_JOBS_POSTPONED_QUEUE
        if (typePostponed == 'thread') or (typePostponed == 'local'):
            qJobsPostponed = 'MeteorServer.%s.%x' % (self._instance_name, self._id_thread)
        elif typePostponed == 'instance':
            qJobsPostponed = 'MeteorServer.%s' % (self._instance_name)
        elif typePostponed == 'global':
            qJobsPostponed = 'MeteorServer'

        self._JobsPostponed_Producer = Producer(queue=RedisPriorityQueue(
            [qJobsPostponed], self._Consumer__queue._redis))

    def _run_calculus(self, request, args, timed=None):
        self._current_job['type'][0] = 'Calculus(%s)' % (request["module"])
        try:
            calc = self._jobs_loader.get_instance(request["module"],
                                                  *args["init_args"],
                                                  module=request["module"],
                                                  **args["init_kwargs"])
            return calc.run(*args["run_args"], **args["run_kwargs"])
        except CalculusPostponed:
            self.send_postponed(request)
            raise

    def send_error(self, simu_id, error_msg):
        self.emit({
            'event': SIMULATION_ERROR,
            'simulation_id': simu_id,
            'error': error_msg
        })

    def send_done(self, simu_id):
        super().send_done(simu_id)
        self.emit({
            'event': RESULTS_AVAILABLE,
            'simulation_id': simu_id
        })

    def send_progress(self, simu_id, time_left, sub_time_left, percent, add_percent, msg):
        super().send_progress(simu_id, time_left, sub_time_left, percent, add_percent, msg)
        self.emit({
            'event': SIMULATION_PROGRESS,
            'simulation_id': simu_id,
            'progress': float(percent),
            'time_left': int(time_left),
            'add_progress': float(add_percent),
            'sub_time_left': int(sub_time_left),
            'message': msg
        })

    def send_postponed(self, request):
        if __debug__:
            logger.debug("Push back JOBS '%s' to the end of the queue", request)
        self._JobsPostponed_Producer.emit(request)
