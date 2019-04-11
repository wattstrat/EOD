import numpy as np

from Calculus.calculus import Calculus
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class WeatherDispatch(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we are a meta calculus
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, years_name, noise_name, weather_type):
        if weather_type is not None and weather_type['type'] == 'faithful':
            weather_inst = self.calculus('Calculus.Weather.Hypotheses.WeatherFaithful')
            myweather = weather_inst(weather_type['years'], years_name)
        else:
            weather_inst = self.calculus('Calculus.Weather.Hypotheses.WeatherVariables')
            myweather = weather_inst(years_name, noise_name)
        return myweather


class WeatherFaithful(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we are a meta calculus
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, years, years_name):
        ret = {'data': {}, 'interpolation': {}}
        varname = self._cache.get_val("weather:variables")
        varname.discard('Nebulosity')
        GenerateWeatherScenario = self.calculus("Simulation.Weather.SpecificYear")
        if len(years) == 1:
            tempyears = years * len(years_name)
        elif len(years) - len(years_name) == 1:
            tempyears = years[:-1]
        elif len(years_name) - len(years) == 1:
            tempyears = years + [years[-1]]
        elif len(years_name) == len(years):
            tempyears = years
        else:
            raise ValueError('abs(len(year) - len(years_name)) > 1 : len(years)=%s and len(years_name)=%s ' %
                             (len(years), len(years_name)))
        for year_name, year in zip(years_name, tempyears):
            ret['data'][year_name] = {}
            ret['interpolation'][year_name] = {}
            for var in varname:
                resWeatherScenario = GenerateWeatherScenario(year, var)
                scena, interpo = self.get_variable(resWeatherScenario, wait_var=True)
                ret['data'][year_name][var] = np.matrix(scena)
                ret['interpolation'][year_name][var] = interpo
        return ret


class WeatherVariables(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we are a meta calculus
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, years_name, noise_name):
        # Generation of the noise
        GetNoise = self.calculus("Simulation.Weather.CurrentNoise")
        # Get a random weather scenario : same args, diff matrix => skip_cache
        GenerateWeatherScenario = self.calculus("Simulation.Weather.PickScenario")
        # Matrix add
        add = self.calculus("Maths.Matrix.Addition")
        mult = self.calculus("Maths.Matrix.ElemMult")
        ret = {'data': {}, 'interpolation': {}}
        varname = self._cache.get_val("weather:variables")

        # Result should be saved, so get a value : put simu_id ?
        for year in years_name:
            ret['data'][year] = {}
            ret['interpolation'][year] = {}
            for var in varname:
                noise = GetNoise(var, year, noise_name)
                resWeatherScenario = GenerateWeatherScenario(year, var)
                scena, interpo = self.get_variable(resWeatherScenario, wait_var=True)
                if var == 'Temperature':
                    ret['data'][year][var] = add(noise, scena, get_numpy_matrix=True)
                else:
                    ret['data'][year][var] = mult(noise, scena, get_numpy_matrix=True)
                ret['interpolation'][year][var] = interpo
        return ret
