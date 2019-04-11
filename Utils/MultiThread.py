import threading

# From http://stackoverflow.com/questions/13610654/
#       how-to-make-built-in-containers-sets-dicts-lists-thread-safe/13618333#13618333


class LockProxy(object):
    def __init__(self, obj):
        self.__obj = obj
        # RLock because object methods may call own methods
        self.__lock = threading.RLock()

    def __getattr__(self, name):
        def wrapped(*a, **k):
            with self.__lock:
                return getattr(self.__obj, name)(*a, **k)
        return wrapped
