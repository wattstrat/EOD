
from Config.config import cleanup_coeff_time, cleanup_coeff_poids, cleanup_threshold_mem

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DefaultCleanup(object):
    def __init__(self, *args, listedData=None, **kwargs):
        self._coeff_time = kwargs.get('coeff_time', cleanup_coeff_time)
        self._coeff_poids = kwargs.get('coeff_poids', cleanup_coeff_poids)
        self._threshold_mem = kwargs.get('threshold_mem', cleanup_threshold_mem)
        self._listedData = listData

    def _cleanup_data(self, obj, *args, **kwargs):
        if type(obj) is str:
            obj = getattr(self, obj)

        list_key = self.compute_list(obj, obj._metadata)
        for k in list_key:
            if __debug__:
                logger.debug("Deleting %s", k)
            obj.del_val(k)

    def compute_list(self, obj, metadata):
        max_t = max(metadata.values(), key=lambda md: md["timestamp_read"])
        min_t = min(metadata.values(), key=lambda md: md["timestamp_read"])
        ecart_t = max_t["timestamp_read"] - min_t["timestamp_read"]

        def zero_div(p, q):
            if q == 0:
                return 0
            return p/q

        list_ponderation = [(k, self._coeff_time * zero_div((md["timestamp_read"]-min_t["timestamp_read"]), ecart_t) +
                             self._coeff_poids * md["poids"])
                            for k, md in metadata.items() if not md.get("keep", False)]
        slist_ponderation = sorted(list_ponderation, key=lambda k: k[1])

        ret = []
        if self._threshold_mem is not None and "_obj_size" in obj.__dict__:
            # We are in a SizedData for Object : could compute size of object
            # Assume 100% mem for RAM
            cent = obj._size
            cur = cent
            for (k, p) in slist_ponderation:
                cur -= obj._obj_size[k]
                percent = cur / cent
                if __debug__:
                    logger.debug("Deleting %s, pond:%d, size:%d, occupation:%f", k, p, obj._obj_size[k], percent)
                ret.append(k)
                if percent < self._threshold_mem:
                    break
        else:
            if __debug__:
                logger.debug("Deleting %s, pond:%s", [k for (k, d) in slist_ponderation if d < 1],
                             [d for (k, d) in slist_ponderation if d < 1])
            ret = [k for (k, d) in slist_ponderation if d < 1]

        return ret

    def _cleanup(self, *args, **kwargs):
        for data in self._listedData:
            self._cleanup_data(data, *args, **kwargs)


class DefaultRAMDBCleanup(DefaultCleanup):
    def __init__(self, *args, **kwargs):
        super().__init__(listedData=['_cache_ram', '_cache_db'])
