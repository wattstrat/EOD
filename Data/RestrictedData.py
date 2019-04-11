

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class RestrictedError(Exception):
    pass


class RestrictedData(object):
    """
    Restricted Data is an wrapper to an Data to restrict which variable
    could be asked
    """

    def __init__(self, data, restricted, *args, **kwargs):
        super().__init__()

        self._data = data
        self._restricted = restricted

    def get_val(self, varName, *args, **kwargs):
        if varName in self._restricted:
            return self._data.get_val(varName, *args, **kwargs)
        raise KeyError(varName)

    def in_cache(self, varName):
        return self._data.in_cache(varName)

    def rename(self, varName, newName):
        if varName in self._restricted:
            return self._data.rename(varName, newName)
        raise KeyError(varName)

    def set_val(self, varName, value, *args, **kwargs):
        if varName in self._restricted:
            return self._data.set_val(varName, value, *args, **kwargs)
        raise RestrictedError("%s could not be writted by me" % (varName))

    def del_val(self, varName, *args, **kwargs):
        if varName in self._restricted:
            return self._data.del_val(varName, *args, **kwargs)
        raise KeyError(varName)

    # Should be catch by __getattr__ ?
    # def __sizeof__(self):
    #     return self._data.__sizeof__()

    # def __len__(self):
    #     return self._data.__len__()
    #
    def clear(self):
        self._data.clear()

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return getattr(self._data, name)
