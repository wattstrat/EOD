import re
import numpy as np
import datetime
from dateutil import parser as datetimeparser

from Calculus.calculus import Calculus
from Calculus.CalcVar import CalcVar
import Config.variables as variables
import Config.config as config
from Utils.Numpy import div0
from Utils.deltas import deltaYears
if __debug__:
    import logging
    logger = logging.getLogger(__name__)
else:
    import warnings

ALL_SECTORS = [
    'Demand_Agriculture_Animals',
    'Demand_Agriculture_Plants',
    'Demand_Industry_Efficiency',
    'Demand_Transport_Freight',
    'Demand_Transport_People',
    'Demand_Residential_Cooking',
    'Supply_Electricitygrid_Fatal_HydroRun',
    'Supply_Electricitygrid_Fatal_PV',
    'Supply_Electricitygrid_Fatal_Wind',
    'Demand_Residential_Airconditioning',
    'Demand_Residential_Airing',
    'Demand_Residential_Equipments',
    'Demand_Residential_Heating',
    'Demand_Residential_Lighting',
    'Demand_Residential_Waterheating',
    'Demand_Tertiary_Airconditioning',
    'Demand_Tertiary_Heating',
    'Demand_Tertiary_Lighting',
    'Demand_Tertiary_Specificuse',
    'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_PV',
    'Supply_Electricitygrid_Wind',
    'Supply_Gasgrid',
    'Supply_Heatgrid_Sources']

SECTORS_TO_AVOID = [
    'Supply_Electricitygrid_Dispatchable',
    'Supply_Gasgrid',
    'Supply_Heatgrid_Sources',
    'Demand_Agriculture_Animals',
    'Demand_Agriculture_Plants',
    'Demand_Industry_Efficiency',
    'Demand_Transport_Freight_Air',
    'Demand_Transport_Freight_Rail',
    'Demand_Transport_Freight_Road',
    'Demand_Transport_People_Air',
    'Demand_Transport_People_Rail',
    'Demand_Transport_People_Road',
    'Demand_Residential_Cooking',
    'Demand_Residential_Airconditioning',
    'Demand_Residential_Airing',
    'Demand_Residential_Equipments',
    'Demand_Residential_Heating',
    'Demand_Residential_Lighting',
    'Demand_Residential_Waterheating',
    'Demand_Tertiary_Airconditioning',
    'Demand_Tertiary_Heating',
    'Demand_Tertiary_Lighting',
    'Demand_Tertiary_Specificuse',
]

SECTORS_DEPEND = ['Supply_Electricitygrid_Dispatchable']


class Simulation(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because Simulation are meta-calculus
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, request):
        ret = []
        percent = 0
        self._simu_id = request['simulation_id']
        self._subscription = request['subscription_name']
        maxPercent = request.get('percent', 100)
        correctionPercent = maxPercent / 100

        if __debug__:
            logger.info('Running simulation id %s with subscription %s', self._simu_id, self._subscription)
        else:
            # Disable numpy error print
            np.seterr(all="ignore")
            # Disable warning
            warnings.simplefilter("ignore")

        SendProgress = self.calculus('Simulation.SendProgress')

        # Depend really on the simulation, skip the cache

        extractParam = self.calculus('Simulation.ExtractSimulationParameters')
        # Meta calculus, skip the cache
        constructIndepVariables = self.calculus('Simulation.IndependantsVariables')

        # Extract value in dict for simulation and construct initial param matrix
        if __debug__:
            logger.info('Saving Parameters')
        self._cache.set_val('SimuParameters:%s' % (self._simu_id), request['parameters'])

        # Start/End of our slice
        start = datetimeparser.parse(request['Framing_Perimeter']['period']['start'])
        stop = datetimeparser.parse(request['Framing_Perimeter']['period']['end'])

        milestones_date = []
        # Convert milestones to date
        for milestone in request['Framing_Perimeter']['pertinent_milestones']:
            milestones_date.append(datetimeparser.parse(milestone))

        paramsSimu = extractParam(request, milestones_date)

        workingPercent = config.extractParamPerCent * correctionPercent
        percent = percent + workingPercent
        SendProgress([paramsSimu], add_percent=workingPercent, message='Parameter Variables Extracted')

        if __debug__:
            logger.debug("Value of params : %s", paramsSimu)
        # Constructs variables for all simu like weather
        workingPercent = config.constructIndepVarPerCent * correctionPercent
        percent += workingPercent
        if __debug__:
            logger.info('Construction Independants Variables')
        # independantsVariables = constructIndepVariables(percent, npercent,
        independantsVariables = constructIndepVariables(request, request['Framing_Perimeter'], milestones_date)
        SendProgress([independantsVariables], add_percent=workingPercent,
                     message='Independants Variables Constructed')

        # TODO : change : save using request['parameters'] ?
        saveAllParams = self.calculus('Simulation.SaveAllParams')
        saveAllParams(paramsSimu, independantsVariables)
        # Step into Temporal evolution foreach frame
        nframe = 1

        orderSectors = self._cache.get_val('varname:order')
        orderSectors = self.remove_sectors(orderSectors, SECTORS_TO_AVOID + config.depend_post_first)
        # For now, some sectors are avoid => recalculation of delta_percent
        percent_for_sector = maxPercent - percent
        percent_for_sector -= ((config.PERCENT_FOR_SUMMARY + config.PERCENT_FOR_SUMMARY2) * correctionPercent)
        # Last indexing
        percent_for_sector -= correctionPercent
        delta_percent_sector = percent_for_sector
        nbSector1 = len(ALL_SECTORS) - len(SECTORS_TO_AVOID)
        if (nbSector1 + len(SECTORS_DEPEND)) == 0:
            part_sector = 0
        else:
            part_sector = nbSector1 / (nbSector1 + len(SECTORS_DEPEND))
        delta_percent = delta_percent_sector * part_sector
        delta_percent_sector -= delta_percent
        calcSectors = self.calculus('Simulation.CalcSectors', delta_percent=delta_percent, save_calculus=True)
        # send progress inside calcSectors because of multithreading
        # self.progress(percent=percent, message='Calculating Perimeters Consumptions')
        # npercent = percent + delta_percent
        retval = calcSectors(start, stop, paramsSimu, independantsVariables, orderSectors, 'all')
        ret.append(retval)
        # percent = npercent

        # dependSummary = [ret]

        Summary = self.calculus('Simulation.Summary', depends=ret, depds_recurse=True)
        sumret = []

        SUMMARY_PERCENT = (config.PERCENT_FOR_SUMMARY * correctionPercent)

        percent = SUMMARY_PERCENT / deltaYears.number_step(1, start, stop)
        for delta in deltaYears(1, start, stop):
            retsum = Summary(percent, delta[0].year)
            sumret.append(retsum)
        ret += sumret

        Secondary = self.calculus('Simulation.Demand.Residential.Secondary', depends=sumret, depds_recurse=True)
        secret = []
        for delta in deltaYears(1, start, stop):
            dispret1 = Secondary(delta[0].year)
            secret.append(dispret1)
        ret += secret

        # dependSummary2 = [secret]

        Summary2 = self.calculus('Simulation.Summary', depends=secret, depds_recurse=True)
        sumret2 = []

        SUMMARY_PERCENT = (config.PERCENT_FOR_SUMMARY * correctionPercent)

        percent = SUMMARY_PERCENT / deltaYears.number_step(1, start, stop)
        for delta in deltaYears(1, start, stop):
            retsum = Summary2(percent, delta[0].year, mytype='post-secondary')
            sumret2.append(retsum)
        ret += sumret2

        delta_percent = delta_percent_sector
        calcDependSect = self.calculus('Simulation.CalcDependSectors', delta_percent=delta_percent,
                                       depends=sumret2, depds_recurse=True, save_calculus=True)
        dispret2 = calcDependSect(start, stop, paramsSimu, independantsVariables, [SECTORS_DEPEND], 'all')
        ret.append(dispret2)

        Heatgrid = self.calculus('Simulation.Supply.Heatgrid.Sources', depends=[dispret2], depds_recurse=True)
        sumretheat = []
        for delta in deltaYears(1, start, stop):
            sumretheat1 = Heatgrid(delta[0].year, paramsSimu, paramsIndepVar=independantsVariables)
            sumretheat.append(sumretheat1)
        ret += sumretheat

        Summary = self.calculus('Simulation.Summary', depends=sumretheat, depds_recurse=True)
        sumret3 = []

        SUMMARY_PERCENT = (config.PERCENT_FOR_SUMMARY * correctionPercent)

        percent = SUMMARY_PERCENT / deltaYears.number_step(1, start, stop)
        for delta in deltaYears(1, start, stop):
            retsum = Summary(percent, delta[0].year, mytype='ges')
            sumret3.append(retsum)
        ret += sumret3

        IndexingResults = self.calculus('Simulation.IndexingResults', add_percent=correctionPercent,
                                        message_progress='Indexing',
                                        depends=sumret3, depds_recurse=True)
        index = IndexingResults()
        ret.append(index)

        if __debug__:
            logger.info('Simulation for %s is "done" - indexing', self._simu_id)

        SimuDone = self.calculus('Simulation.SimulationDone', depends=[index], depds_recurse=True)
        end = SimuDone(maxPercent)
        ret.append(end)

        return ret

    def remove_sectors(self, sectors, to_remove):
        filtered_sectors = []
        for sector_group in sectors:
            filtered_group = []
            for sector in sector_group:
                if sector not in to_remove:
                    filtered_group.append(sector)
        filtered_sectors.append(filtered_group)
        return filtered_sectors


# Send signal when simulation is over
class SimulationDone(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we need to send message
        self._skip_cache = True
        self._skip_hash = True
        # Recursivly check dependancies!
        self._depds_recurse = True

    def _run(self, full_percent):
        # All deps is OK, set simulation to DONE!
        if self._simu_id is None:
            return None
        self._cache.set_val('Simulation:%s:done' % (self._simu_id), True)
        if self._meteor is None:
            return None
        if __debug__:
            logger.info('Simulation %s done', self._simu_id)

        # TODO in AWS : keep trac of each percent= to count SimuDone and set percent correctly
        self.progress(message="Simulation done", percent=full_percent)
        send_done = getattr(self._meteor, 'send_done', None)
        if callable(send_done):
            send_done(self._simu_id)
            return True
        return None


# send progress to frontend when depends is OK
class SendProgress(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we need to send message
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, depends, percent=-1, message="", add_percent=-1, time_left=-1, sub_time_left=-1):
        self._check_list_dep(depends)

        # All deps is OK, send progression
        self.progress(time_left=time_left, sub_time_left=sub_time_left,
                      percent=percent, add_percent=add_percent,
                      message=message)
        return True

    def _check_list_dep(self, lst):
        if lst is None:
            return
        if isinstance(lst, list):
            for var in lst:
                self._check_list_dep(var)
            return
        self.get_variable(lst)


# set var to True if depends is OK
class SetVarDepends(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we need to send message
        self._skip_cache = True
        self._skip_hash = True

    def _run(self, depends, varname, message=None):
        self._check_list_dep(depends)
        self._cache.set_val(varname, True)
        if message is not None:
            if __debug__:
                logger.debug(message)

        return True

    def _check_list_dep(self, lst):
        if isinstance(lst, list):
            for var in lst:
                self._check_list_dep(var)
            return
        self.get_variable(lst)


# TODO : percent/npercent
class CalcSectors(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we need to save result in mongo
        self._skip_cache = True
        self._skip_hash = True
        self._delta_percent = kwargs.get("delta_percent", 0)

    def _run(self, start, stop, paramsSimu, paramsIndepVar, order, current_sector):
        length = sum([len(sv) for sv in order])
        if length < 1:
            length = 1
        delta_percent = self._delta_percent / length
        calcSector = self.calculus('Simulation.CalcSector', delta_percent=delta_percent)
        calcSectors = self.calculus('Simulation.CalcSectors', delta_percent=delta_percent)
        SetVarDepends = self.calculus('Simulation.SetVarDepends')
        ret = {}

        if __debug__:
            logger.info('Executing for sector %s', current_sector)
        wait_var = []
        for set_var in order:
            if __debug__:
                logger.info('Executing for sectors %s', set_var)
            for varname in set_var:
                if isinstance(varname, tuple):
                    ret[varname[0]] = calcSectors(start, stop, paramsSimu, paramsIndepVar, varname[1], varname[0])
                    varname = varname[0]
                else:
                    ret[varname] = calcSector(start, stop,
                                              varname, paramsSimu,
                                              paramsIndepVar=paramsIndepVar)
                wait_var.append(ret[varname])
        # OK, set we are done
        SetVarDepends(True, 'CalcSectors:%s:%s:done' % (self._simu_id, current_sector),
                      "CalcSectors of %s from simu %s is done" % (self._simu_id, current_sector))
        return ret


# TODO : percent/npercent
class CalcSector(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we need to save simu result in mongo
        self._skip_cache = True
        self._skip_hash = True
        self._delta_percent = kwargs.get("delta_percent", 0)

    def _run(self, start, stop, param_variable, paramsSimu, **kwargs):

        # TODO : percent / npercent via __init__, calc percent/npercent of StepTemporalEvolution
        SetVarDepends = self.calculus('Simulation.SetVarDepends')
        StepTemporalEvolution = self.calculus('Simulation.StepTemporalEvolution', delta_percent=self._delta_percent)
        if __debug__:
            logger.info('Calculating sector %s', param_variable)
        # Extract name of the calculation to do
        var = param_variable.split('_')
        calc_name = 'Simulation.%s' % ('.'.join(var))

        paramsSimuVal = self.get_variable(paramsSimu)
        # extract params simulations from matrix
        params_mats = self.get_variable(paramsSimuVal["param_matrix"])
        (mats, params) = CalcSector._get_params(calc_name, params_mats, kwargs)
        retval = StepTemporalEvolution(calc_name, param_variable,
                                       start,
                                       stop,
                                       mats,
                                       **params)
        SetVarDepends(True, 'CalcSector:%s:%s:done' % (self._simu_id, param_variable),
                      "CalcSector of %s from simu %s is done" % (self._simu_id, param_variable))
        return retval

    @staticmethod
    def _get_params(calc_name, param_mats, kwargs):
        calcClass = variables.jobs_calculs.get_class(calc_name)
        try:
            requested_matrices = calcClass.params_simu
        except AttributeError:
            if __debug__:
                logger.warning('No attribute params_simu for %s', calc_name)
            requested_matrices = []
        try:
            requested_indep = calcClass.params_indep
        except AttributeError:
            if __debug__:
                logger.warning('No attribute params_indep for %s', calc_name)
            requested_indep = []
        retMat = {req: param_mats[req] for req in requested_matrices}
        retOthers = {req: kwargs['paramsIndepVar'][req] for req in requested_indep}

        return (retMat, retOthers)


class StepTemporalEvolution(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cur_delta = kwargs.get('cur_delta', None)
        self._deltas = kwargs.get('deltas', config.deltas)
        self._delta_percent = kwargs.get('delta_percent', 0)
        self._stop_percent = kwargs.get('stop_percent', 0)

    def _run(self, calc_name, param_variable, start, stop, paramsSimu, **others_params):
        if __debug__:
            logger.info('Time Step %s => %s', start.isoformat(), stop.isoformat())
        SendProgress = self.calculus('Simulation.SendProgress')
        instance_sector = self.calculus(calc_name, seed=start.year)
        # InitSector = self.calculus('Simulation.Results.InitSector')
        # Save sector to mongo, so should be done
        SaveSector = self.calculus('Simulation.Results.SaveSector')
        # Update sector
        UpdateSector = self.calculus('Simulation.Results.UpdateSector')

        delta_step = self._deltas[0]
        delta_others = self._deltas[1:]
        calc = delta_step is config.calc_delta or len(delta_others) == 0
        ret = []
        delta_percent = self._delta_percent / delta_step.number_step(1, start, stop)

        StepTemporalEvolutionMethod = config.STEPTEMPORAL.get(delta_step,
                                                              {'meth': 'Simulation.StepTemporalEvolution',
                                                               'save': False})
        StepTemporalEvolution = self.calculus(StepTemporalEvolutionMethod['meth'],
                                              save_calculus=StepTemporalEvolutionMethod['save'],
                                              delta_percent=delta_percent, cur_delta=delta_step, deltas=delta_others)
        result = None

        # In case of metaSector, param_variables is aliased now!
        sector_variable = config.metasector_to_sectorname.get(param_variable, param_variable)
        if self._cur_delta is config.save_delta or self._cur_delta in config.save_inter_delta:
            result = 'to_be_initialized'  # InitSector(start, sector_variable)
        startb = start
        # from Utils.deltas import deltaHours
        # if delta_step == deltaHours:
        #     startb = stop - datetime.timedelta(hours=24)
        for (step_start, step_stop) in delta_step(1, startb, stop):
            if __debug__:
                logger.debug('Running step %s => %s for %s', step_start, step_stop, calc_name)
            if calc:
                if __debug__:
                    logger.debug('Running computation of %s', calc_name)
                retval = (step_start,
                          instance_sector(step_start, step_stop,
                                          paramsSimu, **others_params))
            else:
                retval = StepTemporalEvolution(calc_name, param_variable,
                                               step_start, step_stop,
                                               paramsSimu,
                                               **others_params)
            if result is None:
                if __debug__:
                    logger.debug('No result, append to ret (%s)', calc_name)
                ret.append(retval)
            else:
                if __debug__:
                    logger.info('Update sector for %s for %s', calc_name, step_start)
                result = UpdateSector(start, sector_variable, result, retval)

        if result is None:
            return ret

        if self._cur_delta is not None and self._cur_delta is config.save_delta:
            if __debug__:
                logger.info('Save sector for %s for %s', calc_name, start)
            # Save sectors in mongo
            SaveSector(start, sector_variable, result)
            # We have saved the value in the mongo, Destroy big matrix but return a value to be saved!
            result = True

        if self._cur_delta is not None and self._cur_delta is config.save_delta:
            # Send progress only if we return splitted result
            SendProgress(result, add_percent=self._delta_percent,
                         message="Sector %s year %s calculated" % (calc_name, self._cur_delta.to_string(start)))

        return result


class IndependantsVariables(Calculus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always skip hash/cache because we are a meta calculus
        self._skip_cache = True
        self._skip_hash = True

#    def _run(self, percent, npercent, param):
    def _run(self, request, perim, milestones):
        # Computation of weather parameters : use random weather
        WeatherVariables = self.calculus('Simulation.Params.WeatherVariables')
        # Computation of demography parameters : use default demo
        DemoVariables = self.calculus('Simulation.Params.DemoVariables')

        # Discard 'category' / 'subcategory' / 'territory_groups' in each param
        res = {}
        # Weather
        start = datetimeparser.parse(perim['period']['start'])
        end = datetimeparser.parse(perim['period']['end'])
        simu_type = request.get('simu_type')
        real_start = datetimeparser.parse(perim['period']['real_start'])
        real_end = datetimeparser.parse(perim['period']['real_end'])
        weather_type = perim.get('weather_type', None)
        clim_scenar = perim.get('climate_scenario', config.default_weather_scenario)

        years_name = [year for year in config.save_delta(1, start, end)]
        res['weather'] = WeatherVariables(years_name, clim_scenar, weather_type)
        res['time_scope'] = {'start': start, 'end': end,
                             'real_start': real_start, 'real_end': real_end,
                             'years_name': years_name, 'simu_type': simu_type,
                             'milestones': milestones}
        res['demography'] = DemoVariables(res['time_scope'], perim['demography'])
        res['economy'] = perim['ecogrowth']
        res['milestones'] = milestones
        # No other indep variables for now

        return res
