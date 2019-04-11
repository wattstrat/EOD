
from DB.DB import DB
from redis import Redis as PyRedis
import Config.config as config

"""
This class represent a Redis abstraction, using redis package.
All functions taken to redis whith error gesture.
"""


class Redis(DB):

    """
    This function initialize all Redis variables.
    _error, _error_message : errors variables, there are set to None.
    __redis, redis: represent Redis client instance.
    _queue_name, queue_name : string who representing the redis queue_name.
    """

    def __init__(self, queue_name=config.REDIS_QUEUE_NAME_SAAS_TO_METEOR, redis=None):
        self._error = None
        self._error_message = None

        if not redis:
            redis = PyRedis()

        self._redis = redis
        self._queue_name = queue_name
