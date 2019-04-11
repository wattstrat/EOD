
import time

from Calculus.calculus import Calculus
import Config.variables as variables
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class PrintJob(Calculus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._kwargs = kwargs
        self._args = args

    def run(self, *args, **kwargs):
        # TODO: check input from client for security, via SCHEMA ?
        if 'message' in self._kwargs:
            if __debug__:
                logger.info(self._kwargs["message"].format(*self._args, **self._kwargs))
        else:
            if __debug__:
                logger.debug("No message to print")


class SleepJob(Calculus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._kwargs = kwargs
        self._args = args

    def run(self, *args, **kwargs):
        tsleep = self._kwargs.get("sleep", 30)
        if __debug__:
            logger.info("Sleeping %d seconds", tsleep)
        time.sleep(tsleep)


class LongMathJob(Calculus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._math1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
        self._math2 = [[1, 2], [1, 2], [3, 4]]

    def run(self, *args, **kwargs):
        try:
            calc = variables.calculs.get_instance("Calculus.Maths.Matrix.Multiplication", skip_cache=False)
            val = calc.run(self._math1, self._math2)
            time.sleep(30)
            if __debug__:
                logger.info("Calculation done : %s", val)
            if val['status'] == "OK":
                if val.get("cached", False):
                    if __debug__:
                        logger.debug("Value is cached => not saving")
                else:
                    self._cache.set_val(val['hash'], val['value'])
            else:
                if __debug__:
                    logger.error("ERROR without exception: %s", val['status'])
            self._cache.set_val("%s:status" % (val['hash']), val['status'])
        except CalculusError as e:
            if __debug__:
                logger.warning("ERROR in doing calculus Calculus.Maths.Matrix.Multiplication")
        except CalculusPostponed as e:
            if __debug__:
                logger.info("POSTPONED calculus Calculus.Maths.Matrix.Multiplication")
        return None
