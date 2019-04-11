
from Calculus.Constant
from DB.DB import DB
from DB.Mongo.Mongo import Mongo
from DB.Redis.Redis import Redis
from Calculus.calculus import Calculus

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DBConstants(Calculus):

    """
        StaticsConstants: list of variable that are contant.
    """

    def __init__(self, *args, **kwargs):
        """    Initialization function.

        """
        super().__init__(*args, **kwargs)
        self._ndb = kwargs.get("db", "Mongo")
        if isinstance(self._ndb, DB):
            self._db = self._nbd
            self._ndb = self._db.name()
        else:
            if self._ndb == "Mongo":
                self._db = Mongo(**kwargs)
            elif self._ndb == "Redis":
                self._db = Redis(**kwargs)
            else:
                raise ValueError("%s is not a correct value to the DB parameter : set it to an instance of DB.DB "
                                 "or to 'Redis' or 'Mongo' string" % (self._ndb))

    def get_val(self, varName, *args, **kwargs):
        """
           Get the constante value"
        """
        super().get_val(varName, *args, **kwargs)
        return self._db.find(key=varName, **kwargs)

    def set_val(self, varName, value, *args, **kwargs):
        """
           Set the constante value to another value"
           WARNING: in Mongo, upsert is by default False,
           so if constants is missing, no value will be added
           pass upsert=True in kwargs
        """
        if __debug__:
            logger.debug(" Calculus.Constants.DBConstants: setting value %s to %s", varName, value)
        val = self._db.update(key=varName, value=value, **kwargs)
        super().set_val(varName, value, *args, **kwargs)
        return val

    def del_val(self, varName, *args, **kwargs):
        super().del_val(varName, *args, **kwargs)
        self._db.delete(key=varName, **kwargs)
