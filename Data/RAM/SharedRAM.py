
from Data.RAM.RAM import RAM
from Utils.RWPLock import RWLock
from Utils.Singleton import NamedSingleton


if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class SharedRAM(NamedSingleton):
    class _impl(RAM):
        """ Shared RAM is an RAM with RWLock which prioritize Writer. """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._rwlock = RWLock()

        def in_cache(self, varName):
            with self._rwlock.reader():
                ret = RAM.in_cache(self, varName)
            return ret

        def rename(self, varName, newName):
            with self._rwlock.writer():
                ret = RAM.rename(self, varName, newName)
            return ret

        def get_val(self, varName, *args, **kwargs):
            with self._rwlock.reader():
                ret = RAM.get_val(self, varName, *args, **kwargs)
            return ret

        def set_val(self, varName, value, *args, **kwargs):
            with self._rwlock.writer():
                ret = RAM.set_val(self, varName, value, *args, **kwargs)
            return ret

        def del_val(self, varName, *args, **kwargs):
            with self._rwlock.writer():
                ret = RAM.del_val(self, varName, *args, **kwargs)
            return ret

        def clear(self):
            with self._rwlock.writer():
                ret = RAM.clear(self)
            return ret

    def __init__(self, *args, **kwargs):
        name = kwargs.get("name", "default")
        super().__init__(name, *args, **kwargs)


class VariablesSharedRAM(NamedSingleton):
    class _impl(RAM):
        """ Shared RAM is an RAM with RWLock which prioritize Writer. """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._rwlock = {}

        def in_cache(self, varName):
            if varName in self._rwlock:
                return True
            else:
                return False

        def rename(self, varName, newName):
            lock = self._rwlock[varName]
            with lock.writer():
                ret = RAM.rename(self, varName, newName)
            self._rwlock[newName] = lock
            del self._rwlock[varName]
            return ret

        def get_val(self, varName, *args, **kwargs):
            lock = self._rwlock[varName]
            with lock.reader():
                ret = RAM.get_val(self, varName, *args, **kwargs)
            return ret

        def set_val(self, varName, value, *args, **kwargs):
            lock = self._rwlock.get(varName, None)
            if lock is None:
                lock = RWLock()
                self._rwlock[varName] = lock

            with lock.writer():
                ret = RAM.set_val(self, varName, value, *args, **kwargs)
            return ret

        def del_val(self, varName, *args, **kwargs):
            lock = self._rwlock[varName]
            with lock.writer():
                ret = RAM.del_val(self, varName, *args, **kwargs)
            del self._rwlock[varName]
            return ret

        def clear(self):
            for var, lock in self._rwlock.items():
                with lock.writer():
                    RAM.del_val(self, var)
            self._rwlock = {}
            return RAM.clear(self)

    def __init__(self, *args, **kwargs):
        name = kwargs.get("name", "default")
        super().__init__(name, *args, **kwargs)
