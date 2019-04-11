
from Data.data import Data

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class RAM(Data):

    """ RAM is an initialized db, i.e. in the RAM. """

    def __init__(self, *args, **kwargs):
        """ Initialization function
        initial : possible internal cache values to be passed
        """
        super().__init__(*args, **kwargs)
        self._cache_dict = kwargs.get('initial', {})

    def in_cache(self, varName):
        return (varName in self._cache_dict)

    def rename(self, varName, newName):
        """ Set varName: value to cache dictionnary. """
        if __debug__:
            logger.debug("Renaming RAM var '%s' into '%s'", varName, newName)
        Data.rename(self, varName, newName)
        try:
            val = self._cache_dict.pop(varName)
        except KeyError:
            raise KeyError("Renaming variable error! No such variable : %s" % (varName))

        self._cache_dict[varName] = val

    def get_val(self, varName, *args, **kwargs):
        """ Return varName's value from cache dictionnary """
        if __debug__:
            logger.debug("Getting RAM var '%s'", varName)
        if varName is not None:
            Data.get_val(self, varName, *args, **kwargs)
            returned_value = self._cache_dict[varName]
        else:
            returned_value = None
        if __debug__:
            logger.debug("  => Return value '%s'", returned_value)
        return returned_value

    def set_val(self, varName, value, *args, **kwargs):
        """ Set varName: value to cache dictionnary. """
        if __debug__:
            logger.debug("Setting RAM var '%s' with '%s'", varName, value)
        Data.set_val(self, varName, value, *args, **kwargs)
        self._cache_dict[varName] = value
        return value

    def del_val(self, varName, *args, **kwargs):
        '''
        delete the variable varName from the cache dictionnary
        '''
        if __debug__:
            logger.debug("Deletting RAM var '%s'", varName)
        returned_value = self._cache_dict[varName]
        Data.del_val(self, varName, *args, **kwargs)
        del self._cache_dict[varName]
        return returned_value

    def clear(self):
        '''
        clear all the value stored
        '''
        if __debug__:
            logger.debug("Clearing RAM")
        super().clear()
        self._cache_dict = {}
