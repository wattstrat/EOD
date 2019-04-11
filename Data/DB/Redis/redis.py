
import json

from redis import Redis as PyRedis

from Data.DB.db import DB
from babel.messages import RESULTS_AVAILABLE
from babel.queue import Producer, RedisQueue, Consumer
import Config.config as config


class Redis(DB):

    """
            This class going to deal with a Redis database.
    """

    def __init__(self, **kwargs):
        """
                Initialize class variables
        """
        try:
            self.redis = PyRedis(host=config.REDIS_HOST, port=config.REDIS_PORT)
            outgoing_queue = RedisQueue(
                config.OUTGOING_COMMUNICATION_QUEUE, self.redis)
            ingoing_queue = RedisQueue(config.INGOING_COMMUNICATION_QUEUE, self.redis)
            self.producer = Producer(outgoing_queue)
            self.consumer = Consumer(ingoing_queue)
        except Exception:
            raise ValueError("Error during redis setup")
