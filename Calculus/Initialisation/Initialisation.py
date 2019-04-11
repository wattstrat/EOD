

from Calculus.calculus import Calculus
import Config.variables as variables


if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Initialisation(Calculus):

    """ Initialisation of Calcul """

    def __init__(self, *args, global_cache=None, **kwargs):
        super().__init__(*args, **kwargs)

        if global_cache is None:
            self._cache = self._cache
        else:
            self._cache = global_cache
