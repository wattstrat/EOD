
from redis import Redis
import time
import random

import Config.config as config

from Server.Meteor.MeteorServer import MeteorServer
from babel.queue import RedisQueue, Producer
from babel.messages import SIMULATION_ERROR, RESULTS_AVAILABLE, SIMULATION_PROGRESS

if __debug__:
    import logging
    logger = logging.getLogger(__name__)

__STEP__ = 10
__SLEEP_STEP__ = 1
__ERROR_RATE__ = 0.02


# A Meteor Server that just receive jobs / simu and discard jobs but return multiple message for ProgressSimu
class MeteorServerBouchon(MeteorServer, Producer):

    def __init__(self, *args, **kwargs):
        """	Initialization class. """
        # Initialise MeteorServer Parent
        super().__init__(**kwargs)

        if __debug__:
            logger.debug("Initialization Bouchon...")

        # = Initialise the Result Queue
        result_queue = [config.OUTGOING_COMMUNICATION_QUEUE]
        # Steal redis instance from Consumer queue
        self._Producer__queue = RedisQueue(result_queue, self._Consumer__queue._redis)

    def _run_jobs(self, request, timed=None):
        if __debug__:
            logger.debug("Discard received Jobs")
        return True

    def _run_simulation(self, request, timed=None):
        if __debug__:
            logger.debug("Launching new Simulation")

        for percent in range(0, 100, __STEP__):
            if random.random() < __ERROR_RATE__:
                self.send_error(request['simulation_id'], "Error processing simulation")
                return False
            self.send_progress(request['simulation_id'], ((100 - percent) / __STEP__) * __SLEEP_STEP__,
                               percent, "En cours")
            time.sleep(__SLEEP_STEP__)
        self.send_done(request['simulation_id'])
        return True

    def send_error(self, simu_id, error_msg):
        self.emit({
            'event': SIMULATION_ERROR,
            'simulation_id': simu_id,
            'error': error_msg
        })

    def send_done(self, simu_id):
        self.emit({
            'event': RESULTS_AVAILABLE,
            'simulation_id': simu_id
        })

    def send_progress(self, simu_id, time_left, percent, msg):
        self.emit({
            'event': SIMULATION_PROGRESS,
            'simulation_id': simu_id,
            'progress': int(percent),
            'time_left': int(time_left),
            'message': msg
        })
