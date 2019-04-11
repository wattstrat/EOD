import numpy as np
import datetime

from calendar import monthrange
import functools

from DB.Mongo.Mongo import Mongo
from Calculus.exceptions import CalculusError
from Calculus.calculus import Calculus

import Config.variables as variables
import Config.config as config
from babel.dot.averaged_variables import weighted_update

import Data.Hypervisor.Politics.ListedDataCalculusPolitic
if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class InitSector(Calculus):
    # InitSector for 1 year in save_delta

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we just create zeros
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, year, calc_name, res):
        """
                Initialize curve and map dictionnary results
        """

        geocodes = self._cache.get_val('geocodes')
        counties = self._cache.get_val('counties')
        if isinstance(res, np.recarray):
            return {"%s_%s" % (calc_name, param): self._init_curve_map(year, geocodes, counties)
                    for param in res.dtype.names}
        elif isinstance(res, np.ndarray):
            # We get the defmatrix from cache => order should come from cache too
            default_matrix_hypothesis_order = self._cache.get_val('Hypothesis:Default:Order')
            return {"%s_%s" % (calc_name, param): self._init_curve_map(year, geocodes, counties)
                    for param in default_matrix_hypothesis_order[calc_name].keys()}
        raise TypeError("Should be an np.recarray or np.ndarray and not a {!s}".format(type(res)))

    def _init_curve_map(self, year, geocodes, counties):
        first_day = datetime.datetime(year=year.year, month=1, day=1, hour=0)
        last_day = datetime.datetime(year=year.year, month=12, day=31, hour=23)

        isocal = last_day.isocalendar()
        if isocal[0] != last_day.year:
            nb_weeks = (last_day - datetime.timedelta(days=isocal[2])).isocalendar()[1] + 1
        else:
            nb_weeks = isocal[1]

        if first_day.isocalendar()[0] != year.year:
            nb_weeks = nb_weeks + 1

        # 0 to ... => + 1
        nb_hours = int((last_day - first_day).total_seconds() / 3600) + 1

        if __debug__:
            logger.debug("Year %d have %d weeks and %d hours", year.year, nb_weeks, nb_hours)
        mapshape = np.zeros((len(geocodes) + len(counties), 13 + nb_weeks))
        curveshape = {county: np.zeros(nb_hours) for county in counties}
        return {"map": mapshape, "curve": curveshape}


# TODO : see results.py
class UpdateSector(Calculus):
    # Update sector for one year (curve/map calibrate to 1 year)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because sector update is dependant of
        # result. Temporal step should return cached value if there is one
        self._skip_cache = True
        self._skip_hash = True
        self.current_month = None
        self.current_year = None
        self.weight_curve = None

    def _run(self, start, calc_name, result, *vals):
        UpdateSector = self.calculus("Simulation.Results.UpdateSector")

        self.counties_ind = self._cache.get_val('counties_indexes')
        self.counties = self._cache.get_val('counties')
        self.geoidx = self._cache.get_val('geocodes_indexes')
        self.calc_name = calc_name

        for val in vals:
            if isinstance(val, list):
                result = UpdateSector(start, calc_name, result, *val)
            elif isinstance(val, tuple):
                result = self._update_curve_map(start, calc_name, result, val)
            else:
                raise CalculusError("vals in UpdateSector should be np.ndarray or list of vals")
        return result

    def _update_curve_map(self, start, calc_name, result, val):
        (hour, res) = val
        if result == 'to_be_initialized':
            InitSector = self.calculus('Simulation.Results.InitSector')
            result = InitSector(start, calc_name, res)

        res = self.get_variable(res)

        if isinstance(res, np.recarray):
            result = self.get_variable(result)
            for param in res.dtype.names:
                varname = "%s_%s" % (calc_name, param)
                self.varname = varname
                value = res[param]
                added_value = self._update_curve(result[varname]["curve"], hour, value)
                value = np.append(value, added_value)
                self._update_map(result[varname]["map"], hour, value)
            return result
        elif isinstance(res, np.ndarray):
            # We get the defmatrix from cache => order should come from cache too
            default_matrix_hypothesis_order = self._cache.get_val('Hypothesis:Default:Order')
            result = self.get_variable(result)
            for param, index in default_matrix_hypothesis_order[calc_name].items():
                varname = "%s_%s" % (calc_name, param)
                self.varname = varname
                value = res[:, index]
                added_value = self._update_curve(result[varname]["curve"], hour, value)
                value = np.append(value, added_value)
                self._update_map(result[varname]["map"], hour, value)
            return result
        raise TypeError("Should be an np.recarray or np.ndarray")

    def _update_curve(self, result, hour, value):
        # Get numerical index of the hour for current year
        # TODO: more general : not current year.
        self.curve_func = self._my_average
        if self.varname in weighted_update:
            if self.weight_curve is None:
                if weighted_update[self.varname]['geo'] == 'population':
                    self.weight_curve = np.array(self._cache.get_val('population'))
                elif weighted_update[self.varname]['geo'] == 'surface':
                    self.weight_curve = np.array(self._cache.get_val('surface'))
                else:
                    self.weight_curve = None
        else:
            self.weight_curve = None
        return self._update_curve_weight(result, hour, value)

    def _my_average(self, value, indices):
        if self.weight_curve is None:
            return np.sum(value[indices])
        else:
            return np.average(value[indices], weights=self.weight_curve[indices])

    def _update_curve_weight(self, result, hour, value):
        first_day = datetime.datetime(year=hour.year, month=1, day=1, tzinfo=hour.tzinfo)
        hour_ind = (hour - first_day).total_seconds() / 3600
        ret_val = []
        for county in self.counties:
            idx_i = self.counties_ind[county]["start"]
            idx_f = self.counties_ind[county]["end"]
            county_val = self.curve_func(value, slice(idx_i, idx_f, None))
            ret_val.append(county_val)
            np.put(result[county], hour_ind, county_val)
        return ret_val

    def _update_map(self, result, hour, value):
        if self.varname in weighted_update and weighted_update[self.varname]['time']:
            if hour.month != self.current_month or hour.year != self.current_year:
                self.current_month = hour.month
                self.current_year = hour.year
                self.weight_month = monthrange(hour.year, hour.month)[1] * 24
            self.weight_map = (8760, self.weight_month, 7 * 24)
        else:
            self.weight_map = (1, 1, 1)
        return self._update_map_weight(result, hour, value)

    def _update_map_weight(self, result, hour, value):
        # Calculate weeknum/month/year index
        isocal = hour.isocalendar()

        if isocal[0] == (hour.year + 1):
            nw = (hour - datetime.timedelta(days=isocal[2])).isocalendar()[1] + 1
        elif isocal[0] == (hour.year - 1):
            # "first" (virtual) week
            nw = 1
        else:
            nw = isocal[1]

            if datetime.datetime(year=hour.year, month=1, day=1).isocalendar()[0] != hour.year:
                # "first" (virtual) week => virtual should be real + 1
                nw = nw + 1

        nw = nw + 12
        ny = 0
        nm = hour.month
        # Year result
        result[:, ny] += value / self.weight_map[0]
        # Month result
        result[:, nm] += value / self.weight_map[1]
        # Week result
        result[:, nw] += value / self.weight_map[2]


class SaveSector(Calculus):

    PIVOT_GEOCODE = None

    def get_pivot(self):
        if SaveSector.PIVOT_GEOCODE is not None:
            return SaveSector.PIVOT_GEOCODE

        geocodes = self._cache.get_val('geocodes')
        for index, geo in enumerate(geocodes):
            # <= PROJECTION_SPLIT_LIMIT => split
            if geo.startswith("FR%s" % (config.PROJECTION_SPLIT_LIMIT + 1)):
                PIVOT_GEOCODE = index
                break

        return PIVOT_GEOCODE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we save result in mogo for client
        self._skip_cache = True
        self._skip_hash = True

        # New connection pool to mongo
        self._mongo = Mongo(database=variables.config["common"]["mongo_db"])

    def _run(self, year, varname, results):
        if __debug__:
            logger.info("Saving %s for simu %s with value(tronc) %.200s", varname, self._simu_id, results)

        # Get constants
        geocodes = self._cache.get_val('geocodes')
        counties = self._cache.get_val('counties')

        territorycodes = geocodes.copy()
        territorycodes.extend(counties)

        geocode_pivot = self.get_pivot()
        for param, result in results.items():
            save = {}

            insert = []
            # Split map
            map_result = result["map"].tolist()
            res = {'projection': 'map_1', 'year': year.year,
                   "varname": param, "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp()}
            res.update(dict(zip(territorycodes[:geocode_pivot], map_result[:geocode_pivot])))

            insert.append(res)
            save['map_1'] = res

            res = {'projection': 'map_2', 'year': year.year,
                   "varname": param, "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp()}

            res.update(dict(zip(territorycodes[geocode_pivot:], map_result[geocode_pivot:])))
            insert.append(res)
            save['map_2'] = res

            # Split curve
            curve_result = result["curve"]
            curve1 = {}
            curve2 = {}

            for county, res in curve_result.items():
                try:
                    if int(county[5:]) <= 50:
                        curve1[county] = res.tolist()
                    else:
                        curve2[county] = res.tolist()
                except ValueError:
                    curve2[county] = res.tolist()

            curve1.update({'projection': 'curve_1', 'year': year.year, "varname": param,
                           "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp()})
            curve2.update({'projection': 'curve_2', 'year': year.year, "varname": param,
                           "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp()})

            insert.append(curve1)
            insert.append(curve2)
            save['curve_1'] = curve1
            save['curve_2'] = curve2
            self._mongo.insert(documents=insert, flag_raw_input=1,
                               database=config.MONGO_SIMULATIONS_DB, collection=self._simu_id)
            if variables.sectorInCache:
                for k, v in save.items():
                    for ids in ['_id', 'projection', 'year', 'varname', 'timestamp']:
                        try:
                            del v[ids]
                        except KeyError:
                            pass
                self._cache.set_val('sector:value:%s:%s' % (param, year.year), save)

        return None


# Indexing results
# TODO Simu Specific...
class IndexingResults(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we need to send message
        self._skip_cache = True
        self._skip_hash = True
        self._always_new = True
        self._message = kwargs.get("message_progress", "Indexing")
        self._percent = kwargs.get("delta_percent")
        # Recursivly check dependancies!
        self._depds_recurse = True
        self._mongo = Mongo(database=variables.config["common"]["mongo_db"])

    def _run(self):
        if __debug__:
            logger.info('Indexing results for %s', self._simu_id)
        SendProgress = self.calculus('Simulation.SendProgress')
        self._mongo.create_index(database=config.MONGO_SIMULATIONS_DB, collection=self._simu_id)
        if self._percent is not None:
            SendProgress(None, add_percent=self._percent, message=self._message)
        return True


# TODO Save all params of simulation : possibility to replay the simulation
class SaveAllParams(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we save params in mogo for client
        self._skip_cache = True
        self._skip_hash = True

        # New connection pool to mongo
        self._mongo = Mongo(database=variables.config["common"]["mongo_db"])

    def _run(self, paramsSimu, independantsVariables):
        if __debug__:
            logger.info("Saving params for simu %s", self._simu_id)
        # """ Insert client hypothesis into mongodb. """
        # final_document = {"varname": "hypothesis"}
        # for sector in self.sectors:
        #     if sector.category:
        #         full_name = sector.name + '_' + sector.category
        #     else:
        #         full_name = sector.name
        #     final_document[full_name] = sector.hypothesis
        # self.data.mongodb.insert(final_document)
        return None
