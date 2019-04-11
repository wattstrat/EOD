from Data.data import Data
from Data.Hypervisor.hypervisor import Hypervisor
from Data.Hypervisor.Politics.CleanupPolitic import DefaultCleanup
from Data.SizedData import MaxSizedData, SizedElementData, ElementMemoryError
from Utils.Exceptions import Exceptions, KeyErrorExceptions
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


# TODO: log error specially in save()
class ListedDataPolitic(Hypervisor):
    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        super().__init__(*args, **kwargs)

        self._caches = []
        self._locals = []
        self._remotes = []
        self._saveAll = kwargs.get("saveAll", True)

        for ind, cache in enumerate(args):
            self._createCache(ind, cache)

        for ind, cache in enumerate(kwargs.get("caches", [])):
            self._createCache(ind, cache)

    def _get_cache(self, cacheName):
        if __debug__:
            logger.debug("Get cache name %s", cacheName)
        return variables.loader.get_class(cacheName)

    def _createCache(self, ind, cache):
        if isinstance(cache, Data):
            cCache = cache
        elif type(cache) is str:
            clCache = self._get_cache(cache)
            cCache = clCache()
        elif type(cache) is dict:
            tyCache = cache["type"]
            clCache = self._get_cache(tyCache)
            cArgs = cache.get("args", [])
            cKwargs = cache.get("kwargs", {})
            cCache = clCache(*cArgs, *cKwargs)
            ElSizedOpt = cache.get("ElSized")
            if ElSizedOpt is not None:
                cCache = SizedElementData(cCache, **ElSizedOpt)
            SizedOpt = cache.get("Sized")
            if SizedOpt is not None:
                cCache = MaxSizedData(cCache, **SizedOpt)
            restricted = cache.get("Restricted")
            if restricted is not None:
                if type(restricted) is str:
                    try:
                        restricted = getattr(config, restricted)
                    except:
                        restricted = [restricted]
                cCache = RestrictedData(cCache, restricted, **restrictedOpt)
            if cache.get("local", False):
                cCache._local = True
            if cache.get("remote", False):
                cCache._remote = True
        else:
            if __debug__:
                logger.warning("Unknown cache option for arg %d: %s", ind, cache)
            return
        self._caches.append(cCache)
        LorR = False
        if getattr(cCache, '_local', False):
            self._locals.append(ind)
            LorR = True
        if getattr(cCache, '_remote', False):
            self._remotess.append(ind)
            LorR = True
        if not LorR:
            # Not local nor Remote: consider local
            self._locals.append(ind)

    def getMetaLR(self, varName, kwargs={}):
        meta = self._metadata.get(varName, {"local": False, "remote": False})
        (L, R) = (kwargs.get("local", meta.get("local", False)), kwargs.get("remote", meta.get("remote", False)))
        if len(self._locals) == 0:
            L = False
        if len(self._remotes) == 0:
            R = False
        return (L, R)

    def setMetaLR(self, varName, local, remote):
        self._metadata[varName].update({"local": local, "remote": remote})
        return (local, remote)

    def in_cache(self, varName):
        (local, remote) = self.getMetaLR(varName)
        return any([self._caches[ind].in_cache(varName) for ind in self._locals]) and \
            (local or not remote or any([self._caches[ind].in_cache(varName) for ind in self._remotes]))

    def rename(self, varName, newName):
        (local, remote) = self.getMetaLR(varName)
        raised = []

        for ind in self._locals:
            try:
                self._caches[ind].rename(varName, newName)
                if __debug__:
                    logger.debug("Renaming %s to %s in local cache[%d]", varName, newName, ind)
            except KeyError as e:
                raised.append(e)

        if not local or remote:
            for ind in self._remotes:
                try:
                    self._caches[ind].rename(varName, newName)
                    if __debug__:
                        logger.debug("Renaming %s to %s in remote cache[%dw]", varName, newName, ind)
                except KeyError as e:
                    raised.append(e)

        if len(raised) == 1:
            raise raised[0]
        if len(raised) > 1:
            raise KeyError(varName)
            if any([isinstance(ex, KeyError) for ex in raised]):
                raise KeyErrorExceptions(varName, raised)
            else:
                raise Exceptions("Multiple exception occured when renaming variable %s to %s" % (varName, newName),
                                 raised)

    def _get(self, indexes, varName, *args, **kwargs):
        get = False
        raised = []
        val = None
        resave = False
        status = None

        for ind in indexes:
            if __debug__:
                logger.debug("Try to get val from Caches[%d] for %s", ind, varName)
            try:
                status = None
                val = self._caches[ind].get_val(varName, *args, **kwargs)
            except KeyError as e:
                if __debug__:
                    logger.debug("Cache %d failed for %s", ind, varName)
                    raised.append(e)
                    resave = True
            else:
                if val is None:
                    # TODO: THIS IS A QUICK FIX
                    # OK, maybe not OK...
                    try:
                        status = self._caches[ind].get_val("%s:status" % varName, *args, **kwargs)
                    except KeyError as e:
                        # no status, should be OK
                        status = 'OK'
                    if status == 'OK':
                        get = True
                        break
                    if __debug__:
                        logger.debug("Value for %s is None and status is %s: check next data in line", varName, status)
                    resave = True
                else:
                    get = True
                    break
                # Another quick ? delete val & status
                try:
                    self._caches[ind].del_val("%s:status" % varName, *args, **kwargs)
                except KeyError:
                    pass
                try:
                    self._caches[ind].del_val(varName, *args, **kwargs)
                except KeyError:
                    pass

        return (get, raised, val, status, resave)

    def get_val(self, varName, *args, **kwargs):
        # logger.critical('G => G:%s', self == variables.cache._LockProxy__obj._DataCalculusPolitic__cache)
        """
        get function. Set the hypervisor's metadata, then tries to access data in RAM, if absent tries in db,
        if absent : error
        If in db, puts it in RAM. In case of memory error tries to make space, if still a problem : error.
        """
        val = None
        (local, remote) = self.getMetaLR(varName, kwargs)
        # use timestamp from metadata to avoid import time and cleaner
        super().get_val(varName, *args, **kwargs)
        raised = []
        get = False
        resave = False
        status = None
        (get, raised, val, status, resave) = self._get(self._locals, varName, *args, **kwargs)

        if not get and (not local or remote):
            if __debug__:
                logger.debug("Getting remote cache for %s", varName)
            (get, raisedR, val, status, resaveR) = self._get(self._remotes, varName, *args, **kwargs)
            raised.extend(raisedR)
            if not get:
                raise KeyError(varName)
                if any([isinstance(ex, KeyError) for ex in raised]):
                    raise KeyErrorExceptions(varName, raised)
                else:
                    raise Exceptions("Exceptions occured when getting variable %s" % (varName), raised)
            resave = True

        if not get:
            raise KeyError(varName)
            if any([isinstance(ex, KeyError) for ex in raised]):
                raise KeyErrorExceptions(varName, raised)
            else:
                raise Exceptions("Exceptions occured when getting variable %s" % (varName), raised)

        if resave:
            if __debug__:
                logger.debug("Resaving value for %s", varName)
            # TODO: write result in one local, all local?
            # For now, let set_val decide
            saveKwargs = kwargs.copy()
            saveKwargs["local"] = True
            saveKwargs["false"] = True
            self.set_val(varName, val, *args, **saveKwargs)
            if status is not None:
                self.set_val("%s:status" % (varName), status, *args, **saveKwargs)

        if __debug__:
            logger.debug("Returning value for %s", varName)

        return val

    def _save(self, indexes, varName, value, *args, **kwargs):
        raised = []
        indRaised = []
        saved = False
        val = None
        if __debug__:
            logger.debug('Saving in indexes %s for %s : save in all: %s', indexes, varName, self._saveAll)
        for ind in indexes:
            try:
                val = self._caches[ind].set_val(varName, value, *args, **kwargs)
                if __debug__:
                    logger.debug('Saved in cache %d for %s', ind, varName)
            except (ElementMemoryError, MemoryError) as e:
                indRaised.append((ind, e))
            else:
                saved = True
                if not self._saveAll:
                    break

        if not saved or self._saveAll:
            # some exception should occured (or not is self._saveAll)
            for (ind, ex) in indRaised:
                if isinstance(ex, ElementMemoryError):
                    # Nothing could be done...
                    pass
                elif isinstance(ex, MemoryError):
                    self._cleanup_data(self._caches[ind])
                    # Try again
                    try:
                        val = self._caches[ind].set_val(varName, value, *args, **kwargs)
                    except (ElementMemoryError, MemoryError) as e:
                        ex = e
                    else:
                        ex = None
                        saved = True
                        if not self._saveAll:
                            break
                else:
                    pass
                if ex is not None:
                    raised.append(ex)

        return (saved, raised, val)

    # TODO A refaire (from RamDbPolitic)
    # TODO for now set to the first non exception
    def set_val(self, varName, value, *args, **kwargs):
        # logger.critical('S => G:%s', self == variables.cache._LockProxy__obj._DataCalculusPolitic__cache)
        super().set_val(varName, value, *args, **kwargs)
        (local, remote) = self.getMetaLR(varName, kwargs)
        self.setMetaLR(varName, local, remote)
        timestamp = self._metadata[varName]["timestamp_write"]

        saved = False
        raised = []

        savedR = False
        raisedR = []

        (saved, raised, val) = self._save(self._locals, varName, value, *args, **kwargs)

        if remote or not local:
            # OK, sould save also in remote
            (savedR, raisedR, valR) = self._save(self._remotes, varName, value, *args, **kwargs)

        combinedRaised = raised + raisedR
        if remote and not savedR:
            # Specify remote and error in remote saving
            raise KeyError(varName)
            if any([isinstance(ex, KeyError) for ex in combinedRaised]):
                raise KeyErrorExceptions(varName, combinedRaised)
            else:
                raise Exceptions("Remote save failed for %s" % (varName), combinedRaised)

        if local and not saved:
            raise KeyError(varName)
            # Specify local and error in local saving
            if any([isinstance(ex, KeyError) for ex in raised]):
                raise KeyErrorExceptions(varName, raised)
            else:
                raise Exceptions("Local save failed for %s" % (varName), raised)

        if not saved and not savedR:
            raise KeyError(varName)
            # Not saved
            if any([isinstance(ex, KeyError) for ex in combinedRaised]):
                raise KeyErrorExceptions(varName, combinedRaised)
            else:
                raise Exceptions("Save failed for %s" % (varName), combinedRaised)

        if __debug__:
            logger.debug('return value from set for %s (%s) => %s', varName, saved, val if saved else valR)
        return val if saved else valR

    def del_val(self, varName, *args, **kwargs):
        # Remove from Remote & Local
        (local, remote) = self.getMetaLR(varName)

        for ind in self._locals:
            try:
                self._caches[ind].del_var(varName, *args, **kwargs)
            except KeyError as e:
                pass

        if not local or remote:
            for ind in self._remotes:
                try:
                    self._caches[ind].del_var(varName, *args, **kwargs)
                except KeyError as e:
                    pass

    def clear(self):
        for cache in self._caches:
            cache.clear()


class ListedDataPoliticWithDefaultCleanup(ListedDataPolitic, DefaultCleanup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._listData = self._caches

    def _cleanup(self, *args, **kwargs):
        L = kwargs.get('local', None)
        R = kwargs.get('remote', None)
        if L is None and R is None:
            super()._cleanup(*args, **kwargs)
        if L:
            for ind in self._locals:
                self._cleanup_data(self._caches[ind], *args, **kwargs)
        if R:
            for ind in self._remotes:
                self._cleanup_data(self._caches[ind], *args, **kwargs)
