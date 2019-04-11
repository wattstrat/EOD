
import Config.config import __STATICS_CONSTANTS__
from Calculus.calculus import Calculus
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class StaticsConstants(Calculus):

    """
        StaticsConstants: list of variable that are contant.
    """

    def __init__(self, *args, constants=__STATICS_CONSTANTS__, **kwargs):
        """    Initialization function.
               _value is the constante value of every value
        """
        super().__init__(*args, **kwargs)
        self._constants = constants

    def get_val(self, varName, *args, **kwargs):
        """
           Get the constante value"
        """
        super().get_val(varName, *args, **kwargs)
        return self._constants[varName]

    def set_val(self, varName, value, *args, **kwargs):
        """
           Set the constante value to another value"
        """
        if __debug__:
            logger.debug(
                " Calculus.StaticsConstants: setting value %s to %s", varName, value)
        self._constants[varName] = value
        super().set_val(varName, value, *args, **kwargs)
        return value

    def del_val(self, varName, *args, **kwargs):
        super().del_val(varName, *args, **kwargs)
        try:
            del self._constants[varName]
        except:
            if __debug__:
                logger.warning(
                    " Calculus.StaticsConstants: no constant named %s", varName)
