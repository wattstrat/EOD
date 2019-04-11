

from Calculus.Constants.Constants import Constants
from Inputs.DB.db import DB as WeatherDB

from Config.config import __WEATHER_COLLECTIONS__, MONGODB_METEOR_DATABASE
import Config.variables as variables
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class WeatherConstants(Constants):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._weather_input = WeatherDB()
        self._poids = 100

    def _run(self):
        self._weather_input.get_sets_reconstruction_numpy(database=MONGODB_METEOR_DATABASE,
                                                          collection=__WEATHER_COLLECTIONS__[7])
        weather_vars = self._weather_input.variable_set
        weather_year = self._weather_input.year_build_set

        self._cache.set_val("weather:variables", weather_vars, poids=self._poids)
        self._cache.set_val("weather:year", weather_year, poids=self._poids)

        return None
