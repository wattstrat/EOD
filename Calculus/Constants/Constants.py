

from Calculus.CalcVar import CalcVar
from Calculus.calculus import Calculus

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class Constants(Calculus):
    def __init__(self, *args, **kwargs):
        """	Initialization function. """
        super().__init__(*args, **kwargs)
        self._poids = 0

    def run(self, *args, **kwargs):
        ret = Calculus.run(self, *args, **kwargs)
        if isinstance(ret, CalcVar):
            ret._poids = self._poids
        return ret
