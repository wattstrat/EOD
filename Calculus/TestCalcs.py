

from Calculus.calculus import Calculus
from Calculus.CalcVar import CalcVar
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class MathMultiple(Calculus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _run(self, mat1, mat2, *args, **kwargs):
        mult = self.calculus("Calculus.Maths.Matrix.Multiplication", skip_cache=False, save_calculation=True)
        add = self.calculus("Calculus.Maths.Matrix.Addition", skip_cache=False, save_calculation=True)
        if __debug__:
            logger.debug("Calculating val1")
        val1 = mult.run([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], [[1, 2], [1, 2], [3, 4]])
        if __debug__:
            logger.debug("   => Result : %s", val1)
        if __debug__:
            logger.debug("Calculating val1bis")
        val1bis = mult.run(CalcVar(value=[[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], serialize=True),
                           CalcVar(value=[[1, 2], [1, 2], [3, 4]], serialize=False))
        if __debug__:
            logger.debug("   => Result : %s", val1bis)
        if __debug__:
            logger.debug("Calculating val2")
        val2 = mult.run([[11, 12, 13], [14, 15, 16], [17, 18, 19], [110, 111, 112]], [[11, 12], [11, 12], [13, 14]])
        if __debug__:
            logger.debug("   => Result : %s", val2)
        if __debug__:
            logger.debug("Calculating val2bis")
        val2bis = mult.run(val2, mat2)
        if __debug__:
            logger.debug("   => Result : %s", val2bis)
        if __debug__:
            logger.debug("Calculating val3")
        val3 = mult.run([[21, 22, 23], [24, 25, 26], [27, 28, 29], [210, 211, 212]], [[21, 22], [21, 22], [23, 24]])
        if __debug__:
            logger.debug("   => Result : %s", val3)
        if __debug__:
            logger.debug("Calculating val3bis")
        val3bis = add.run([[1420,  1480], [1600,  1660], [1780,  1840], [13660, 14260]], val1)
        if __debug__:
            logger.debug("   => Result : %s", val3bis)
        if __debug__:
            logger.debug("Calculating val4")
        val4 = add.run(val3, val2)
        if __debug__:
            logger.debug("   => Result : %s", val4)
        if __debug__:
            logger.debug("Calculating val4bis")
        val4bis = add.run(val3bis, val2)
        if __debug__:
            logger.debug("   => Result : %s", val4bis)
        if __debug__:
            logger.debug("Calculating val5")
        val5 = add.run(val4, val4bis)
        if __debug__:
            logger.debug("   => Result : %s", val5)
        if __debug__:
            logger.debug("Calculating val6")
        val6 = add.run(mat1, val5)
        if __debug__:
            logger.debug("   => Result : %s", val6)
        if __debug__:
            logger.debug("val1bis  => Result : %s", val1bis)
        return val6
