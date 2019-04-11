

import importlib
from Data.data import Data

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DataParameters(object):

    """
    Data Parameters objects, i.e how to calculates varname if not in Caches
    """

    def __init__(self, calcClass=None, className=None,
                 classArgs=None, setArgs=None, getArgs=None, delArgs=None, Args=None):
        """    Initialization function.
        _class is the loaded class
        _fullname is the full path of the class including module
        _args is the arguments to pass to class for initialisation
        """
        super().__init__()
        self._class = calcClass
        self._fullname = className
        self._args = classArgs
        if setArgs is None:
            self._setArgs = Args
        else:
            self._setArgs = setArgs
        if getArgs is None:
            self._getArgs = Args
        else:
            self._getArgs = getArgs
        if delArgs is None:
            self._delArgs = Args
        else:
            self._delArgs = delArgs

    def get_instance(self, preserve=False):
        if isinstance(self._class, Data):
            return self._class
        else:
            calcClass = self.getClass()
            if self._args is not None:
                ret = calcClass(self._args)
            else:
                ret = self._class(self._args)
            if preserve:
                self._class = ret
            return ret

    def get_class(self):
        if self._class is None:
            return self._getFromFullName()
        elif issubclass(self._class, Data):
            return self._class
        else:
            return self._getFromFullName()

    def _get_from_full_name(self):
        if self._fullname is None:
            if __debug__:
                logger.error(
                    " DataParameters._getFromFullName : can not load class fullname is none")
            raise ImportError()
        try:
            module_name, class_name = self._fullname.rsplit('.', 1)
            mod = importlib.import_module(module_name)
            self._class = getattr(mod, class_name)
            if not issubclass(self._class, Data):
                if __debug__:
                    logger.warning(
                        " DataParameters.getClass : loaded class %s is not a subclass of Data.", self._fullname)
                self._class = None
                raise ImportError
            return self._class
        except ImportError as error:
            if __debug__:
                logger.error(" DataParameters.getClass : can not load class %s - ImportError => name: %s, path: %s",
                             self._fullname, error.name, error.path)
            raise
        except Exception as e:
            if __debug__:
                logger.error(
                    " DataParameters.getClass : can not load class %s - "
                    "Unhandle Exception => %s", self._fullname, str(e))
            raise

    def get_class_rgs(self):
        if self._args is None:
            return {}
        else:
            return self._args

    def get_get_args(self):
        if self._getArgs is None:
            return {}
        else:
            return self._getArgs

    def get_set_args(self):
        if self._setArgs is None:
            return {}
        else:
            return self._setArgs

    def get_del_args(self):
        if self._delArgs is None:
            return {}
        else:
            return self._delArgs
