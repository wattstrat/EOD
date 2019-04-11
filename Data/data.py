
import time

__DEFAULT_POIDS__ = 0

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Data(object):

    """
    Data objects, i.e how to access data when trying to compute results.
    """

    def __init__(self, *args, **kwargs):
        """    Initialization function.
        _metadata is a potential initial dictionnary containing values about timestamps
        """
        super().__init__()

        self._metadata = kwargs.get('metadata', {})

    def in_cache(self, varName):
        return (varName in self._metadata)

    def rename(self, varName, newName):
        try:
            val = self._metadata.pop(varName)
        except KeyError:
            raise KeyError("Renaming variable error! No such variable : %s" % (varName))

        self._metadata[newName] = val

    def get_poids(self, varName):
        if self._metadata.get(varName) is None:
            if __debug__:
                logger.debug(" Data.get_poids: Missing metadata : varName = %s", varName)
            pass
        else:
            try:
                return self._metadata[varName]["poids"]
            except KeyError:
                if __debug__:
                    logger.error(" Data.get_poids: Missing poids metadata : varName = %s", varName)
                pass
        return __DEFAULT_POIDS__

    def get_nb_access(self, varName):
        if self._metadata.get(varName) is None:
            if __debug__:
                logger.debug(" Data.get_nb_access: Missing metadata : varName = %s", varName)
            pass
        else:
            try:
                return self._metadata[varName]["nbAccess"]
            except KeyError:
                if __debug__:
                    logger.error(" Data.get_nb_access: Missing nbAccess metadata : varName = %s", varName)
                pass
        return 0

    def get_val(self, varName, *args, **kwargs):
        """
            called by subclass, used to store timestamps of when a variable was accessed
            this is stored in the form of a dictionnary of dictionnaries
            _metadata[varName] = {"timestamp_read" : timestamp, "timestamp_write" : timestamp}
        """

        if varName is not None:
            timestamp = kwargs.pop("timestamp", time.time())
            if self._metadata.get(varName) is None:
                self._metadata[varName] = {
                    "timestamp_read": timestamp, "nbAccess": 1, "poids": __DEFAULT_POIDS__}
            else:
                self._metadata[varName]["timestamp_read"] = timestamp
                self._metadata[varName][
                    "nbAccess"] = self.get_nb_access(varName) + 1

    def set_val(self, varName, value, *args, **kwargs):
        """
            called by subclass, used to store timestamps of when a variable was modified
            this is stored in the form of a dictionnary of dictionnaries
            _metadata[varName] = {"timestamp_read" : timestamp, "timestamp_write" : timestamp}
        """
        if varName is not None:
            timestamp = kwargs.pop("timestamp", time.time())
            self._metadata[varName] = {"timestamp_read": timestamp,
                                       "timestamp_write": timestamp,
                                       "poids": kwargs.get('poids', self.get_poids(varName)),
                                       "nbAccess": self.get_nb_access(varName) + 1}
            self._metadata[varName].update(kwargs.get('metadata', {}))

    def del_val(self, varName, *args, **kwargs):
        '''
        delete the variable varName from the cache dictionnary
        '''
        if varName is not None:
            try:
                del self._metadata[varName]
            except KeyError:
                if __debug__:
                    logger.error(" KeyError in del_val : varName = %s", varName)
                pass

    def clear(self):
        '''
        clear all the value stored
        '''
        self._metadata = {}

    def get_timestamp_read(self, *args, varName=None, **kwargs):
        """ Return varName last update timestamp if varName specified or all data timestamps. """
        if varName is not None:
            return self._metadata[varName]["timestamp_read"]
        return None

    def get_timestamp_write(self, *args, varName=None, **kwargs):
        """ Return varName last update timestamp if varName specified or all data timestamps. """
        if varName is not None:
            return self._metadata[varName]["timestamp_write"]
        return None
