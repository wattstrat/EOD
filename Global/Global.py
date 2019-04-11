
import importlib
import re

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class ClassNotAuthorized(ImportError):
    pass


class ModuleNotAuthorized(ImportError):
    pass


class Global(object):

    def __init__(self, alias={}):

        self._loaded_module = {}
        self._loaded_class = {}
        self._alias = alias

    def get_module(self, module_name):
        """	This method return the module  """
        if module_name in self._loaded_module:
            if __debug__:
                logger.debug("saved imported module '%s'", module_name)
            module = self._loaded_module[module_name]
        else:
            if module_name in self._alias:
                new_module_name = self._alias[module_name]
                if __debug__:
                    logger.debug("Module '%s' aliased to '%s'", module_name, new_module_name)
                module = self.get_module(new_module_name)
            else:
                module = self._import_module(module_name)
            self._loaded_module[module_name] = module
        return module

    def _import_module(self, module_name):
        if __debug__:
            logger.debug("Importing module '%s'", module_name)
        try:
            module = importlib.import_module(module_name)
        except ImportError as error:
            if __debug__:
                logger.critical("Error importing module '%s'", module_name)
            raise
        return module

    def _import_class(self, module, classname):
        if __debug__:
            logger.debug("Loading from module '%s' class '%s'", module, classname)
        module = self.get_module(module)
        if hasattr(module, classname):
            retclass = getattr(module, classname)
        else:
            if __debug__:
                logger.critical("Error importing class '%s' from '%s'", classname, module)
            raise ImportError('%s.%s' % (module, classname))
        return retclass

    def get_class(self, classname):
        if classname in self._loaded_class:
            if __debug__:
                logger.debug("saved imported class '%s'", classname)
            retclass = self._loaded_class[classname]
        else:
            if classname in self._alias:
                new_class_name = self._alias[classname]
                if __debug__:
                    logger.debug("Class '%s' aliased to '%s'", classname, new_class_name)
                retclass = self.get_class(new_class_name)
            else:
                module_name, class_name = classname.rsplit('.', 1)
                retclass = self._import_class(module_name, class_name)
            self._loaded_class[classname] = retclass
        return retclass

    def get_instance(self, classname, *args, **kwargs):
        if __debug__:
            logger.debug("Return new instance of class '%s', args = %s, kwargs = %s", classname, args, kwargs)
        requested_class = self.get_class(classname)
        instance = requested_class(*args, **kwargs)
        instance._aliased_class = classname
        return instance


class GlobalFiltered(Global):

    def __init__(self, alias={}, filters=[]):
        super().__init__(alias)

        self._filters = filters

    def get_module(self, module_name):
        if module_name not in self._filters:
            raise ModuleNotAuthorized("Module '%s' not in authorized module" % (module_name))

        return Global.get_module(self, module_name)

    def get_class(self, classname):
        if classname not in self._filters:
            raise ClassNotAuthorized("Class '%s' not in authorized class" % (classname))

        return Global.get_class(self, classname)


class GlobalREFiltered(Global):

    def __init__(self, alias={}, filters=[]):
        super().__init__(alias)

        self._filters = []
        for filt in filters:
            self._filters.append(re.compile(filt))

    def get_module(self, module_name):
        for filt in self._filters:
            if filt.match(module_name):
                return Global.get_module(self, module_name)

        raise ModuleNotAuthorized("Module '%s' not in authorized module" % (module_name))

    def get_class(self, classname):
        for filt in self._filters:
            if filt.match(classname):
                return Global.get_class(self, classname)

        raise ClassNotAuthorized("Class '%s' not in authorized class" % (classname))
