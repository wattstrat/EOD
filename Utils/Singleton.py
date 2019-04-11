

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class NamedSingleton(object):
    __instance = {}

    class _impl(object):
        pass

    def __init__(self, nameShared, *args, **kwargs):
        single = NamedSingleton.__instance.get(nameShared)
        if single is None:
            NamedSingleton.__instance[nameShared] = self._impl(*args, **kwargs)
        self.__dict__['_NamedSingleton__name'] = nameShared

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        name = self.__dict__['_NamedSingleton__name']
        return getattr(NamedSingleton.__instance[name], attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        name = self.__dict__['_NamedSingleton__name']
        return setattr(NamedSingleton.__instance[name], attr, value)
