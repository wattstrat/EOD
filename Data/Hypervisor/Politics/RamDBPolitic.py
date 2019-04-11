from Data.Hypervisor.hypervisor import Hypervisor
from Data.Hypervisor.Politics.CleanupPolitic import DefaultRAMDBCleanup
from Data.RAM.RAM import RAM
from Data.RAM.SharedRAM import SharedRAM
from Data.SizedData import MaxSizedData, SizedElementData, ElementMemoryError

from Data.DB.Mongo.mongo import Mongo

if __debug__:
    import logging
    logger = logging.getLogger(__name__)
# By default, intialise with Mongo


class RamDBPolitic(Hypervisor):

    def __init__(self, *args, **kwargs):
        """ Initialization function. """
        super().__init__(*args, **kwargs)

        sized_ram_opt = kwargs.get("SizedRAM-opt")
        shared = kwargs.get("shared", False)
        ram_opt = kwargs.get("RAM-opt", {})
        sized_db_opt = kwargs.get("SizedDB-opt")
        db_opt = kwargs.get("DB-opt", {'database': 'CacheDB', 'collection': 'default'})

        ram = kwargs.get("RAM")
        if ram is None:
            if shared:
                self._cache_ram = SharedRAM(**ram_opt)
            else:
                self._cache_ram = RAM(**ram_opt)
        else:
            self._cache_ram = ram
        if sized_ram_opt is not None:
            self._cache_ram = MaxSizedData(self._cache_ram, **sized_ram_opt)

        self._cache_db = kwargs.get("DB", Mongo(**db_opt))

        if sized_db_opt is not None:
            self._cache_db = SizedElementData(self._cache_db, **sized_db_opt)

    def getMetaLR(self, varName, kwargs={}):
        meta = self._metadata.get(varName, {"local": False, "remote": False})
        return (kwargs.get("local", meta.get("local", False)), kwargs.get("remote", meta.get("remote", False)))

    def setMetaLR(self, varName, local, remote):
        self._metadata[varName].update({"local": local, "remote": remote})
        return (local, remote)

    def in_cache(self, varName):
        (local, remote) = self.getMetaLR(varName)
        return self._cache_ram.in_cache(varName) and (local or not remote or self._cache_db.in_cache(varName))

    def rename(self, varName, newName):
        (local, remote) = self.getMetaLR(varName)
        raised = None
        raisedDB = None
        try:
            self._cache_ram.rename(varName, newName)
        except KeyError as e:
            raised = e

        if not local or remote:
            try:
                self._cache_db.rename(varName, newName)
            except KeyError as e:
                raisedDB = e

        if raised is not None and raisedDB is not None:
            raise raised
        if local and raised is not None:
            raise raised
        if remote and raisedDB is not None:
            raise raisedDB

    def get_val(self, varName, *args, **kwargs):
        """
        get function. Set the hypervisor's metadata, then tries to access data in RAM, if absent tries in db,
        if absent : error
        If in db, puts it in RAM. In case of memory error tries to make space, if still a problem : error.
        """
        val = None
        (local, remote) = self.getMetaLR(varName, kwargs)
        # use timestamp from metadata to avoid import time and cleaner
        super().get_val(varName, *args, **kwargs)
        try:
            val = self._cache_ram.get_val(varName, *args, **kwargs)
        except KeyError as e:
            if __debug__:
                logger.debug('No variable named %s in the RAM, checking in db', varName)
            if local:
                raise e
            val = self._cache_db.get_val(varName, *args, **kwargs)
            if val is not None:
                # Try to insert the value in the ram instead
                # and delete from db
                try:
                    self._cache_ram.set_val(
                        varName, val, *args, **kwargs)
                except MemoryError:
                    # RAM Ram return MemoryError
                    if __debug__:
                        logger.warning("No more memory in RAM for %s: Try cleanup", varName)
                    try:
                        self._cleanup_ram(*args, **kwargs)
                        self._cache_ram.set_val(varName, val, *args, **kwargs)
                    except MemoryError:
                        # RAM Ram return MemoryError
                        # even with cleanup
                        if __debug__:
                            logger.warning(" => No more memory in RAM even with cleanup : Keep in DB")
                        pass
        if __debug__:
            logger.debug("  => Return value '%s'", val)
        return val

    # TODO A refaire : MemoryError de la db ou RAM ? Prendre en compte le sizedDB
    def set_val(self, varName, value, *args, **kwargs):
        super().set_val(varName, value, *args, **kwargs)
        (local, remote) = self.getMetaLR(varName, kwargs)
        self.setMetaLR(varName, local, remote)
        timestamp = self._metadata[varName]["timestamp_write"]
        val = None
        try:
            try:
                val = self._cache_ram.set_val(varName, value, *args, **kwargs)
            except ElementMemoryError:
                # RAM do not accept large object : raise
                raise
            except MemoryError:
                # RAM Ram return MemoryError
                if __debug__:
                    logger.warning("No more memory in RAM for %s: Try cleanup", varName)
                try:
                    self._cleanup_ram(*args, **kwargs)
                    self._cache_ram.set_val(varName, value, *args, **kwargs)
                except MemoryError as e:
                    # RAM Ram return MemoryError even with cleanup
                    if local:
                        raise e
                    if __debug__:
                        logger.warning(" => No more memory in RAM even with cleanup : set in DB")
                    val = self._cache_db.set_val(varName, value, *args, **kwargs)
                    return val
            if remote or not local:
                val = self._cache_db.set_val(varName, value, *args, **kwargs)
        except ElementMemoryError as e:
            if remote:
                raise
            if __debug__:
                logger.debug("remote => false : %s", str(e))
        except MemoryError:
            if __debug__:
                logger.warning("No more memory in DB for %s: Try cleanup", varName)
            self._cleanup_db(*args, **kwargs)
            val = self._cache_db.set_val(varName, value, *args, **kwargs)

        return val

    def del_val(self, varName, *args, **kwargs):
        # Remove from DB & RAM
        (local, remote) = self.getMetaLR(varName, kwargs)
        try:
            self._cache_ram.del_val(varName)
        except KeyError:
            if __debug__:
                logger.debug('No variable named %s to be deleted in the RAM', varName)
            pass
        if not local:
            try:
                self._cache_db.del_val(varName)
            except KeyError:
                if __debug__:
                    logger.debug('No variable named %s to be deleted in the db', varName)
                pass

    def clear(self):
        self._cache_ram.clear()
        self._cache_db.clear()


class RamDBPoliticWithDefaultCleanup(RamDBPolitic, DefaultRAMDBCleanup):
    pass
