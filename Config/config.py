
'''
    Global settings file for METEOR
    All basics settings are specified here.
'''

import datetime
import re
from dateutil import parser as datetimeparser

from Utils.deltas import *

# == Version
__GIT_REV__ = 'f5398b1355ce48bc8102e25ca47c95f808d35650'
__VERSION__ = __GIT_REV__

version = 'Meteor Server version %s' % (__VERSION__)

# ==== LOGGING CONFIG ====
LOGCONF_FILENAME = 'logger.conf'
# == END LOGGING CONFIG ==


# ==== LOADER_ALIAS ===
LOADER_ALIAS = {
    # Cache
    'Cache.RAM': 'Data.RAM.RAM.RAM',
    'Cache.SharedRAM': 'Data.RAM.SharedRAM.SharedRAM',
    'Cache.VariablesSharedRAM': 'Data.RAM.SharedRAM.VariablesSharedRAM',
    'Cache.Mongo': 'Data.DB.Mongo.mongo.Mongo',
    'Cache.Politics.RamDBCalculus': 'Data.Hypervisor.Politics.RamDBCalculusPolitic.RamDBCalculusPolitic',
    'Cache.Politics.SizedRamDBCalculus': 'Data.Hypervisor.Politics.RamDBCalculusPolitic.SizedRamDBCalculusPoliticWithDefaultCleanup',
    'Cache.Politics.RamDB': 'Data.Hypervisor.Politics.RamDBPolitic.RamDBPolitic',
    'Cache.Politics.ListedDataCalculus': 'Data.Hypervisor.Politics.ListedDataCalculusPolitic.ListedDataCalculusPolitic',
}
# Weather
default_weather_scenario = 'climate_normal'

TIMERS = True

DEFAULT_VALUE = 4.2**4.2
LIST_DEFAULT_VALUE = [DEFAULT_VALUE, -9999, str(DEFAULT_VALUE), '-9999']
MISSING_DEFAULT_RAW_WEATHER = 999.0
NORMAL_YEAR_NHOUR = 8760
REF_DATE = datetimeparser.parse('2015-01-01T00:00:00.000Z')
DATA_DIR_PATH = '/datas/'

MESSAGE_ENCODING = 'utf-8'
DEFAULT_SLEEP_TIME = 0.1
# minimal timeout : 1s
DEFAULT_REDIS_TIME = 1
NONZERO_VAL = 1e-7

# ==== MONGO CONFIG ====
MONGO_METEOR_DB_NAME = 'TEST'
MONGO_SERVER_PORT = 27017
MONGO_SERVER_ADDRESS = '192.168.1.24'
# AWS :
# MONGO_SERVER_ADDRESS = '172.31.48.142'

# == END MONGO CONFIG ==


MONGO_METEOR_COLLECTIONS = (
    'mainresidences.surfaces',
    'mainresidences.propelants',
    'mainresidences.households',
    'mainresidences.constructions_dates',
    'employees'
)
MONGO_SIMULATIONS_DB = 'simulations'
MONGO_MAX_OBJ_SIZE = 14000000

# ==== REDIS CONFIG QUEUE ====
# TODO: Change queue name
REDIS_QUEUE_NAME_SAAS_TO_METEOR = 'dispatcher_to_meteor'
OUTGOING_COMMUNICATION_QUEUE = 'meteor_to_dispatcher'
INGOING_COMMUNICATION_QUEUE = 'dispatcher_to_meteor'

# local / thread => post for the same thread
# instance       => post for the same instance (same server instance)
# global         => post for the general Queue ("MeteorServer")
# specific / <all>       => specific queue (OUTGOING_JOBS_POSTPONED_QUEUE)
OUTGOING_JOBS_POSTPONED_QUEUE_TYPE = 'instance'

OUTGOING_JOBS_POSTPONED_QUEUE = 'dispatcher_to_meteor'

# TODO: Queue name for jobs to GPU processing jobs => meteor

REDIS_QUEUE_CONF = {
    'queue_name': REDIS_QUEUE_NAME_SAAS_TO_METEOR
}
# == END REDIS CONFIG QUEUE ==

# ==== REDIS CONFIG ====

REDIS_HOST = 'localhost'
# AWS :
# REDIS_HOST = 'redis-prod.nbwhqi.ng.0001.euw1.cache.amazonaws.com'
REDIS_PORT = 6379

REDIS_CONF = {
    'host': REDIS_HOST,
    'port': REDIS_PORT
}
# == END REDIS CONFIG ==

# ==== CACHE CONFIG ====
CACHE_CONF = {
}
# == END CACHE CONFIG ==


# ==== MODULES CONFIG ====

MODULE_CONFIG = {
}

# OCALCULUS_ALIAS = {
CALCULUS_ALIAS = {
    # Config Init classes
    'Init.Total.Computations': 'Calculus.Initialisation.AsyncInit.asyncinit_entrypoint.PerformInsertion',
    'Init.Supply.Capas': 'Calculus.Initialisation.AsyncInit.Supply.electricitygrid.CapasInit',
    'Init.Supply.Heatgrid': 'Calculus.Initialisation.AsyncInit.Supply.heatgrid.PropLossesInit',
    'Init.Demand.Industry': 'Calculus.Initialisation.AsyncInit.Demand.industry.Industry',
    'Init.Demand.Residential': 'Calculus.Initialisation.AsyncInit.Demand.residential.Residential',
    'Init.Demand.Tertiary': 'Calculus.Initialisation.AsyncInit.Demand.tertiary.Tertiary',
    'Init.Demand.Transport': 'Calculus.Initialisation.AsyncInit.Demand.transport.Transport',
    'Init.Demand.Agriculture': 'Calculus.Initialisation.AsyncInit.Demand.agriculture.Agriculture',

    # Main EOD function
    'EOD': 'Calculus.EOD.eod.EOD',
    # Main Evaluation function
    'Evaluation': 'Calculus.Eval.Evaluation.Evaluation',
    # Main Simulation function
    'Simulation': 'Calculus.Simulations.Simulation',
    'Simulation.SendProgress': 'Calculus.Job.DependsJob',
    'Simulation.SimulationDone': 'Calculus.Job.DependsJob',
    'Simulation.SetVarDepends': 'Calculus.Job.DependsJob',
    'Simulation.ExtractSimulationParameters': 'Calculus.ExtractSimuParameters.ExtractSimulationParameters',
    'Simulation.ExtractSimulationMilestoneParameters': 'Calculus.Job.DependsJob',
    'Simulation.TerritoryGroups': 'Calculus.ExtractSimuParameters.TerritoryGroups',
    'Simulation.DefaultValues': 'Calculus.ExtractSimuParameters.DefaultValues',
    'Simulation.IndependantsVariables': 'Calculus.Simulations.IndependantsVariables',
    'Simulation.SaveAllParams': 'Calculus.Results.SaveAllParams',
    'Simulation.CalcSectors': 'Calculus.Simulations.CalcSectors',
    'Simulation.CalcSector': 'Calculus.Simulations.CalcSector',
    'Simulation.StepTemporalEvolution': 'Calculus.Simulations.StepTemporalEvolution',
    'Simulation.StepTemporalEvolution.MT': 'Calculus.Job.WrapperJob',
    'Simulation.Results.InitSector': 'Calculus.Results.InitSector',
    'Simulation.Results.SaveSector': 'Calculus.Results.SaveSector',
    'Simulation.Results.UpdateSector': 'Calculus.Results.UpdateSector',
    'Simulation.Params.WeatherVariables': 'Calculus.Weather.Hypotheses.WeatherDispatch',
    'Simulation.Params.DemoVariables': 'Calculus.Demography.Hypotheses.DemoVariables',
    'Simulation.IndexingResults': 'Calculus.Job.DependsJob',
    'Simulation.Summary': 'Calculus.Job.WrapperJob',
    'Simulation.CalcDependSectors': 'Calculus.Job.DependsJob',
    'Simulation.Summary.SummaryMap': 'Calculus.Job.DependsJob',
    'Simulation.Summary.SummaryKeywords': 'Calculus.Job.DependsJob',
    'Simulation.Summary.SummaryGeocodeMap': 'Calculus.Summary.Summary.SummaryGeocodeMap',
    'Simulation.Summary.SummaryNames': 'Calculus.Summary.SummaryConstants.Static',

    # Weather Generation
    'Simulation.Weather.CurrentNoise': 'Calculus.Weather.Noise.Noise',
    'Simulation.Weather.PickScenario': 'Calculus.Weather.Scenario.WeatherPick',
    'Simulation.Weather.Interpolate': 'Calculus.Weather.Interpolate.HourlyInterpolation',
    'Simulation.Weather.SpecificYear': 'Calculus.Weather.Scenario.SpecificYear',

    # Math object
    'Maths.Vector.Sum': 'Calculus.Maths.Vector.VectorSumNumpy',
    'Maths.Vector.Addition': 'Calculus.Maths.Vector.VectorAdditionNumpy',
    'Maths.Vector.Addition.InPlace': 'Calculus.Maths.Vector.VectorAdditionInPlaceNumpy',
    'Maths.Matrix.Multiplication': 'Calculus.Maths.Matrix.MatrixMultiplicationNumpy',
    'Maths.Matrix.Addition': 'Calculus.Maths.Matrix.MatrixAdditionNumpy',
    'Maths.Matrix.ElemMult': 'Calculus.Maths.Matrix.MatrixElemMultNumpy',

    # FOR TEST!
    # Meta Sector for demand
    'Simulation.Global.Weather': 'Calculus.Weather.WeatherStorage.WeatherStorage',
    'Simulation.Demand.Industry.Efficiency': 'Calculus.Demand.Industry.Industry.Efficiency',
    'Simulation.Demand.Residential.Secondary': 'Calculus.Demand.Residential.Secondary.Secondary',
    'Simulation.Demand.Residential.Airconditioning': 'Calculus.Demand.Residential.Residential.Airconditioning',
    'Simulation.Demand.Residential.Equipments': 'Calculus.Demand.Residential.Residential.Equipments',
    'Simulation.Demand.Residential.Cooking': 'Calculus.Demand.Residential.Residential.Cooking',
    'Simulation.Demand.Residential.Heating': 'Calculus.Demand.Residential.Residential.Heating',
    'Simulation.Demand.Residential.Airing': 'Calculus.Demand.Residential.Residential.Airing',
    'Simulation.Demand.Residential.Lighting': 'Calculus.Demand.Residential.Residential.Lighting',
    'Simulation.Demand.Residential.Waterheating': 'Calculus.Demand.Residential.Residential.Waterheating',
    'Simulation.Demand.Tertiary.Airconditioning': 'Calculus.Demand.Tertiary.Tertiary.Airconditioning',
    'Simulation.Demand.Tertiary.Heating': 'Calculus.Demand.Tertiary.Tertiary.Heating',
    'Simulation.Demand.Tertiary.Lighting': 'Calculus.Demand.Tertiary.Tertiary.Lighting',
    'Simulation.Demand.Tertiary.Specificuse': 'Calculus.Demand.Tertiary.Tertiary.Specificuse',
    'Simulation.Demand.Agriculture.Animals': 'Calculus.Demand.Agriculture.Agriculture.Animals',
    'Simulation.Demand.Agriculture.Plants': 'Calculus.Demand.Agriculture.Agriculture.Plants',
    'Simulation.Supply.Electricitygrid.Fatal.PV': 'Calculus.Supply.Electricitygrid.FatalProd.PVProd',
    'Simulation.Supply.Electricitygrid.Fatal.Wind': 'Calculus.Supply.Electricitygrid.FatalProd.WindProd',
    'Simulation.Supply.Electricitygrid.Fatal.HydroRun': 'Calculus.Supply.Electricitygrid.FatalProd.HydroRunProd',
    'Simulation.Supply.Electricitygrid.Dispatchable': 'Calculus.Supply.Electricitygrid.DispatchableProd.DispatchableProd',
    'Simulation.Supply.Electricitygrid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Capacity': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Sources': 'Calculus.Supply.Heatgrid.heatgrid.Sources',
    'Simulation.Supply.Heatgrid.Localisation': 'Calculus.Supply.Heatgrid.heatgrid.Localisation',
    'Simulation.Supply.Gasgrid.Power': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Gasgrid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',

    # Demand
    'Simulation.Demand.Residential.Consumption.Heating': 'Calculus.Demand.Residential.Consumption.Heating',
    'Simulation.Demand.Residential.Renovation': 'Calculus.Demand.Residential.Renovation.Renovation',
    'Simulation.Demand.Residential.Consumption.Equipments': 'Calculus.Demand.Residential.Consumption.Equipments',
    'Simulation.Demand.Residential.Consumption.Cooking': 'Calculus.Demand.Residential.Consumption.Cooking',
    'Simulation.Demand.Residential.Consumption.Airconditioning': 'Calculus.Demand.Residential.Consumption.Airconditioning',
    'Simulation.Demand.Residential.Consumption.Lighting': 'Calculus.Demand.Residential.Consumption.Lighting',
    'Simulation.Demand.Residential.Consumption.Airing': 'Calculus.Demand.Residential.Consumption.Airing',
    'Simulation.Demand.Residential.Consumption.Waterheating': 'Calculus.Demand.Residential.Consumption.Waterheating',
    'Simulation.Demand.Residential.Construction': 'Calculus.Demand.Residential.Construction.Construction',
    'Simulation.Demand.Residential.LegacyConstruction': 'Calculus.Demand.Residential.Construction.LegacyConstruction',
    'Simulation.Demand.Tertiary.Construction': 'Calculus.Demand.Tertiary.Construction',
    'Simulation.Demand.Tertiary.Construction.Surfaces': 'Calculus.Demand.Tertiary.Construction.Surfaces',
    'Simulation.Demand.Tertiary.Construction.ACSurfaces': 'Calculus.Demand.Tertiary.Construction.ACSurfaces',
    'Simulation.Demand.Tertiary.Construction.HeatSurfaces': 'Calculus.Demand.Tertiary.Construction.HeatSurfaces',
    'Simulation.Demand.Tertiary.Renovation.Thermal': 'Calculus.Demand.Tertiary.Renovation.Thermal',
    'Simulation.Demand.Tertiary.Consumption.Airconditioning': 'Calculus.Demand.Tertiary.Consumption.Airconditioning',
    'Simulation.Demand.Tertiary.Consumption.Heating': 'Calculus.Demand.Tertiary.Consumption.Heating',
    'Simulation.Demand.Tertiary.Consumption.Lighting': 'Calculus.Demand.Tertiary.Consumption.Lighting',
    'Simulation.Demand.Tertiary.Consumption.Specificuse': 'Calculus.Demand.Tertiary.Consumption.Specificuse',
    'Simulation.Demand.Industry.Consumption.Efficiency': 'Calculus.Demand.Industry.Consumption.Efficiency',
    'Simulation.Demand.Transport.Infrastructure.Infrastructure': 'Calculus.Demand.Transport.Infrastructure.Infrastructure',
    'Simulation.Demand.Transport.People.Road': 'Calculus.Demand.Transport.Transport.PeopleRoad',
    'Simulation.Demand.Transport.People.Rail': 'Calculus.Demand.Transport.Transport.PeopleRail',
    'Simulation.Demand.Transport.People.Air': 'Calculus.Demand.Transport.Transport.PeopleAir',
    'Simulation.Demand.Transport.Freight.Road': 'Calculus.Demand.Transport.Transport.FreightRoad',
    'Simulation.Demand.Transport.Freight.Rail': 'Calculus.Demand.Transport.Transport.FreightRail',
    'Simulation.Demand.Transport.Freight.Air': 'Calculus.Demand.Transport.Transport.FreightAir',
    'Simulation.Demand.Transport.Freight.Traffic': 'Calculus.Demand.Transport.Freight.Traffic',
    'Simulation.Demand.People.Road': 'Calculus.Demand.Transport.People.Road',
    'Simulation.Demand.People.Rail': 'Calculus.Demand.Transport.People.Rail',
    'Simulation.Demand.People.Air': 'Calculus.Demand.Transport.People.Air',
    'Simulation.Demand.Freight.Road': 'Calculus.Demand.Transport.Freight.Road',
    'Simulation.Demand.Freight.Rail': 'Calculus.Demand.Transport.Freight.Rail',
    'Simulation.Demand.Freight.Air': 'Calculus.Demand.Transport.Freight.Air',
    'Simulation.Demand.Transport.Freight.Traffic': 'Calculus.Demand.Transport.Freight.Traffic',
    'Simulation.Demand.Transport.People.Mobility': 'Calculus.Demand.Transport.People.Mobility',

    # Simulation.Supply
    'Simulation.Supply.Electricitygrid.Production.Fatal': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Production.Dispatchable': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Grid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Storage.Capacity': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Gasgrid.Production.Power': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Gasgrid.Grid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Production.Power': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Grid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.FatalProd.Wind': 'Calculus.Supply.Electricitygrid.FatalProd.WindProd',
    'Simulation.Supply.FatalProd.PVProd': 'Calculus.Supply.Electricitygrid.FatalProd.PVProd',
    'Simulation.Supply.FatalProd.HydroRunProd': 'Calculus.Supply.Electricitygrid.FatalProd.HydroRunProd',
    'Simulation.Supply.Electricitygrid.Dispatchable.Param': 'Calculus.Initialisation.Hypothesis.supply.DispatchableParam',

}

CALCULUS_MODULES = [
    'Calculus\..*',
    'Simulation\..*',
    'Simulation',
    'Maths\..*',
    'Init\..*',
    'Scripts\..*',
]

# CALCULUS_ALIAS = \
JOBSCALCULUS_ALIAS = {
    # Config Init classes
    'Init.Total.Computations': 'Calculus.Initialisation.AsyncInit.asyncinit_entrypoint.PerformInsertion',
    'Init.Supply.Capas': 'Calculus.Initialisation.AsyncInit.Supply.electricitygrid.CapasInit',
    'Init.Supply.Heatgrid': 'Calculus.Initialisation.AsyncInit.Supply.heatgrid.PropLossesInit',
    'Init.Demand.Industry': 'Calculus.Initialisation.AsyncInit.Demand.industry.Industry',
    'Init.Demand.Residential': 'Calculus.Initialisation.AsyncInit.Demand.residential.Residential',
    'Init.Demand.Tertiary': 'Calculus.Initialisation.AsyncInit.Demand.tertiary.Tertiary',
    'Init.Demand.Transport': 'Calculus.Initialisation.AsyncInit.Demand.transport.Transport',
    'Init.Demand.Agriculture': 'Calculus.Initialisation.AsyncInit.Demand.agriculture.Agriculture',

    # Main EOD function
    'EOD': 'Calculus.EOD.eod.EOD',
    # Main Evaluation function
    'Evaluation': 'Calculus.Eval.Evaluation.Evaluation',
    # Main Simulation function
    'Simulation': 'Calculus.Simulations.Simulation',
    'Simulation.SendProgress': 'Calculus.Simulations.SendProgress',
    'Simulation.SimulationDone': 'Calculus.Simulations.SimulationDone',
    'Simulation.DefaultValues': 'Calculus.ExtractSimuParameters.DefaultValues',
    'Simulation.SetVarDepends': 'Calculus.Simulations.SetVarDepends',
    'Simulation.CalcDependSectors': 'Calculus.Simulations.CalcSectors',
    'Simulation.ExtractSimulationParameters': 'Calculus.ExtractSimuParameters.ExtractSimulationParameters',
    'Simulation.ExtractSimulationMilestoneParameters': 'Calculus.ExtractSimuParameters.ExtractSimulationMilestoneParameters',
    'Simulation.TerritoryGroups': 'Calculus.ExtractSimuParameters.TerritoryGroups',
    'Simulation.IndependantsVariables': 'Calculus.Simulations.IndependantsVariables',
    'Simulation.SaveAllParams': 'Calculus.Results.SaveAllParams',
    'Simulation.CalcSectors': 'Calculus.Simulations.CalcSectors',
    'Simulation.CalcSector': 'Calculus.Simulations.CalcSector',
    'Simulation.StepTemporalEvolution': 'Calculus.Simulations.StepTemporalEvolution',
    'Simulation.StepTemporalEvolution.MT': 'Calculus.Simulations.StepTemporalEvolution',
    'Simulation.Results.InitSector': 'Calculus.Results.InitSector',
    'Simulation.Results.SaveSector': 'Calculus.Results.SaveSector',
    'Simulation.Results.UpdateSector': 'Calculus.Results.UpdateSector',
    'Simulation.Params.WeatherVariables': 'Calculus.Weather.Hypotheses.WeatherDispatch',
    'Simulation.Params.DemoVariables': 'Calculus.Demography.Hypotheses.DemoVariables',

    'Simulation.IndexingResults': 'Calculus.Results.IndexingResults',
    'Simulation.Summary': 'Calculus.Summary.Summary.SummaryFromKeywordsWithIndexing',
    'Simulation.Summary.SummaryKeywords': 'Calculus.Summary.SummaryConstants.StaticKeywords',
    'Simulation.Summary.SummaryMap': 'Calculus.Summary.Summary.SummaryMapByMatrixQueryAllVarWithCache',
    'Simulation.Summary.SummaryGeocodeMap': 'Calculus.Summary.Summary.SummaryGeocodeMap',
    'Simulation.Summary.SummaryNames': 'Calculus.Summary.SummaryConstants.Static',

    # Weather Generation
    'Simulation.Weather.CurrentNoise': 'Calculus.Weather.Noise.Noise',
    'Simulation.Weather.PickScenario': 'Calculus.Weather.Scenario.WeatherPick',
    'Simulation.Weather.Interpolate': 'Calculus.Weather.Interpolate.HourlyInterpolation',

    # Math object
    'Maths.Vector.Sum': 'Calculus.Maths.Vector.VectorSumNumpy',
    'Maths.Vector.Addition': 'Calculus.Maths.Vector.VectorAdditionNumpy',
    'Maths.Vector.Addition.InPlace': 'Calculus.Maths.Vector.VectorAdditionInPlaceNumpy',
    'Maths.Matrix.Multiplication': 'Calculus.Maths.Matrix.MatrixMultiplicationNumpy',
    'Maths.Matrix.Addition': 'Calculus.Maths.Matrix.MatrixAdditionNumpy',
    'Maths.Matrix.ElemMult': 'Calculus.Maths.Matrix.MatrixElemMultNumpy',

    # FOR TEST!

    # Meta Sector for demand
    'Simulation.Global.Weather': 'Calculus.Weather.WeatherStorage.WeatherStorage',
    'Simulation.Demand.Industry.Efficiency': 'Calculus.Demand.Industry.Industry.Efficiency',
    'Simulation.Demand.Residential.Secondary': 'Calculus.Demand.Residential.Secondary.Secondary',
    'Simulation.Demand.Residential.Airconditioning': 'Calculus.Demand.Residential.Residential.Airconditioning',
    'Simulation.Demand.Residential.Airing': 'Calculus.Demand.Residential.Residential.Airing',
    'Simulation.Demand.Residential.Equipments': 'Calculus.Demand.Residential.Residential.Equipments',
    'Simulation.Demand.Residential.Cooking': 'Calculus.Demand.Residential.Residential.Cooking',
    'Simulation.Demand.Residential.Heating': 'Calculus.Demand.Residential.Residential.Heating',
    'Simulation.Demand.Residential.Lighting': 'Calculus.Demand.Residential.Residential.Lighting',
    'Simulation.Demand.Residential.Waterheating': 'Calculus.Demand.Residential.Residential.Waterheating',
    'Simulation.Demand.Tertiary.Airconditioning': 'Calculus.Demand.Tertiary.Tertiary.Airconditioning',
    'Simulation.Demand.Tertiary.Heating': 'Calculus.Demand.Tertiary.Tertiary.Heating',
    'Simulation.Demand.Tertiary.Lighting': 'Calculus.Demand.Tertiary.Tertiary.Lighting',
    'Simulation.Demand.Tertiary.Specificuse': 'Calculus.Demand.Tertiary.Tertiary.Specificuse',
    'Simulation.Demand.Agriculture.Animals': 'Calculus.Demand.Agriculture.Agriculture.Animals',
    'Simulation.Demand.Agriculture.Plants': 'Calculus.Demand.Agriculture.Agriculture.Plants',
    'Simulation.Supply.Electricitygrid.Fatal.PV': 'Calculus.Supply.Electricitygrid.FatalProd.PVProd',
    'Simulation.Supply.Electricitygrid.Fatal.HydroRun': 'Calculus.Supply.Electricitygrid.FatalProd.HydroRunProd',
    'Simulation.Supply.Electricitygrid.Fatal.Wind': 'Calculus.Supply.Electricitygrid.FatalProd.WindProd',
    'Simulation.Supply.Electricitygrid.Dispatchable': 'Calculus.Supply.Electricitygrid.DispatchableProd.DispatchableProd',
    'Simulation.Supply.Electricitygrid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Capacity': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Sources': 'Calculus.Supply.Heatgrid.heatgrid.Sources',
    'Simulation.Supply.Heatgrid.Localisation': 'Calculus.Supply.Heatgrid.heatgrid.Localisation',
    'Simulation.Supply.Gasgrid.Power': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Gasgrid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    # Demand

    'Simulation.Demand.Residential.Consumption.Heating': 'Calculus.Demand.Residential.Consumption.Heating',
    'Simulation.Demand.Residential.Renovation': 'Calculus.Demand.Residential.Renovation.Renovation',
    'Simulation.Demand.Residential.Consumption.Airing': 'Calculus.Demand.Residential.Consumption.Airing',
    'Simulation.Demand.Residential.Consumption.Equipments': 'Calculus.Demand.Residential.Consumption.Equipments',
    'Simulation.Demand.Residential.Consumption.Cooking': 'Calculus.Demand.Residential.Consumption.Cooking',
    'Simulation.Demand.Residential.Consumption.Airconditioning': 'Calculus.Demand.Residential.Consumption.Airconditioning',
    'Simulation.Demand.Residential.Consumption.Lighting': 'Calculus.Demand.Residential.Consumption.Lighting',
    'Simulation.Demand.Residential.Consumption.Waterheating': 'Calculus.Demand.Residential.Consumption.Waterheating',
    'Simulation.Demand.Residential.Construction': 'Calculus.Demand.Residential.Construction.Construction',
    'Simulation.Demand.Residential.LegacyConstruction': 'Calculus.Demand.Residential.Construction.LegacyConstruction',
    'Simulation.Demand.Tertiary.Construction': 'Calculus.Demand.Tertiary.Construction',
    'Simulation.Demand.Tertiary.Construction.Surfaces': 'Calculus.Demand.Tertiary.Construction.Surfaces',
    'Simulation.Demand.Tertiary.Construction.ACSurfaces': 'Calculus.Demand.Tertiary.Construction.ACSurfaces',
    'Simulation.Demand.Tertiary.Construction.HeatSurfaces': 'Calculus.Demand.Tertiary.Construction.HeatSurfaces',
    'Simulation.Demand.Tertiary.Renovation.Thermal': 'Calculus.Demand.Tertiary.Renovation.Thermal',
    'Simulation.Demand.Tertiary.Consumption.Airconditioning': 'Calculus.Demand.Tertiary.Consumption.Airconditioning',
    'Simulation.Demand.Tertiary.Consumption.Heating': 'Calculus.Demand.Tertiary.Consumption.Heating',
    'Simulation.Demand.Tertiary.Consumption.Lighting': 'Calculus.Demand.Tertiary.Consumption.Lightinf',
    'Simulation.Demand.Tertiary.Consumption.Specificuse': 'Calculus.Demand.Tertiary.Consumption.Specificuse',
    'Simulation.Demand.Industry.Consumption.Efficiency': 'Calculus.Demand.Industry.Consumption.Efficiency',
    'Simulation.Demand.Transport.Freight.Road': 'Calculus.Demand.Transport.Transport.FreightRoad',
    'Simulation.Demand.Transport.Freight.Rail': 'Calculus.Demand.Transport.Transport.FreightRail',
    'Simulation.Demand.Transport.Freight.Air': 'Calculus.Demand.Transport.Transport.FreightAir',
    'Simulation.Demand.Transport.Infrastructure.Infrastructure': 'Calculus.Demand.Transport.Infrastructure.Infrastructure',
    'Simulation.Demand.Transport.People.Road': 'Calculus.Demand.Transport.Transport.PeopleRoad',
    'Simulation.Demand.Transport.People.Rail': 'Calculus.Demand.Transport.Transport.PeopleRail',
    'Simulation.Demand.Transport.People.Air': 'Calculus.Demand.Transport.Transport.PeopleAir',
    'Simulation.Demand.People.Road': 'Calculus.Demand.Transport.People.Road',
    'Simulation.Demand.People.Rail': 'Calculus.Demand.Transport.People.Rail',
    'Simulation.Demand.People.Air': 'Calculus.Demand.Transport.People.Air',
    'Simulation.Demand.Freight.Road': 'Calculus.Demand.Transport.Freight.Road',
    'Simulation.Demand.Freight.Rail': 'Calculus.Demand.Transport.Freight.Rail',
    'Simulation.Demand.Freight.Air': 'Calculus.Demand.Transport.Freight.Air',
    'Simulation.Demand.Transport.Freight.Traffic': 'Calculus.Demand.Transport.Freight.Traffic',
    'Simulation.Demand.Transport.People.Mobility': 'Calculus.Demand.Transport.People.Mobility',

    # Simulation.Supply
    'Simulation.Supply.Electricitygrid.Production.Fatal': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Production.Dispatchable': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Grid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Electricitygrid.Storage.Capacity': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Gasgrid.Production.Power': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Gasgrid.Grid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Production.Power': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.Heatgrid.Grid.Gridchange': 'Calculus.Test.Ones.MatricesCalcSector',
    'Simulation.Supply.FatalProd.HydroRunProd': 'Calculus.Supply.Electricitygrid.FatalProd.HydroRunProd',
    'Simulation.Supply.FatalProd.PVProd': 'Calculus.Supply.Electricitygrid.FatalProd.PVProd',
    'Simulation.Supply.FatalProd.HydroRunProd': 'Calculus.Supply.Electricitygrid.FatalProd.HydroRunProd',
    'Simulation.Supply.Electricitygrid.Dispatchable.Param': 'Calculus.Initialisation.Hypothesis.supply.DispatchableParam',
}

metasector_to_sectorname = {
    'Demand_Industry_Efficiency': 'Demand_Industry_Consumption_Efficiency',
    'Demand_Residential_Airconditioning': 'Demand_Residential_Consumption_Airconditioning',
    'Demand_Residential_Airing': 'Demand_Residential_Consumption_Airing',
    'Demand_Residential_Equipments': 'Demand_Residential_Consumption_Equipments',
    'Demand_Residential_Cooking': 'Demand_Residential_Consumption_Cooking',
    'Demand_Residential_Heating': 'Demand_Residential_Consumption_Heating',
    'Demand_Residential_Lighting': 'Demand_Residential_Consumption_Lighting',
    'Demand_Residential_Waterheating': 'Demand_Residential_Consumption_Waterheating',
    'Demand_Tertiary_Airconditioning': 'Demand_Tertiary_Consumption_Airconditioning',
    'Demand_Tertiary_Heating': 'Demand_Tertiary_Consumption_Heating',
    'Demand_Tertiary_Lighting': 'Demand_Tertiary_Consumption_Lighting',
    'Demand_Tertiary_Specificuse': 'Demand_Tertiary_Consumption_Specificuse',
    'Demand_Transport_Freight_Road': 'Demand_Transport_Freight_Road',
    'Demand_Transport_Freight_Rail': 'Demand_Transport_Freight_Rail',
    'Demand_Transport_Freight_Air': 'Demand_Transport_Freight_Air',
    'Demand_Transport_People_Road': 'Demand_Transport_People_Road',
    'Demand_Transport_People_Rail': 'Demand_Transport_People_Rail',
    'Demand_Transport_People_Air': 'Demand_Transport_People_Air',
    'Demand_Agriculture_Animals': 'Demand_Agriculture_Consumption_Animals',
    'Demand_Agriculture_Plants': 'Demand_Agriculture_Consumption_Plants',
    # Simulation.Supply
    'Supply_Electricitygrid_Gridchange': 'Supply_Electricitygrid_Grid_Gridchange',
    'Supply_Electricitygrid_Capacity': 'Supply_Electricitygrid_Storage_Capacity',
    'Supply_Gasgrid_Power': 'Supply_Gasgrid_Production_Power',
    'Supply_Gasgrid_Gridchange': 'Supply_Gasgrid_Grid_Gridchange',
    'Supply_Heatgrid_Power': 'Supply_Heatgrid_Production_Power',
    'Supply_Heatgrid_Gridchange': 'Supply_Heatgrid_Grid_Gridchange',

}
STEPTEMPORAL = {
    deltaYears: {'meth': 'Simulation.StepTemporalEvolution.MT', 'save': True}
    # deltaYears: {'meth': 'Simulation.StepTemporalEvolution', 'save': False}
}
JOBSCALCULUS_MODULES = [
    'Calculus\..*',
    'Simulation\..*',
    'Simulation',
    'Maths\..*',
    'Init\..*',
    'Scripts\..*',
]

JOBS_IMPLEMENTED = [
    'Calculus.TestJobs.PrintJob',
    'Calculus.TestJobs.SleepJob',
    'Calculus.TestJobs.LongMathJob',
    'Calculus.TestJobs',
    'Calculus.Maths.Matrix.MatrixMultiplicationPython',
    'Calculus.Maths.Matrix.MatrixMultiplicationNumpy',
    'Calculus.Maths.Matrix.Multiplication',
    'Calculus.Maths.Matrix',
    'Calculus.Maths',
    'Calculus.Job.CalculJob',
    'Calculus.Job.WrapperJob',
    'Calculus.Job',
    'Calculus.Initialisation.AsyncInit.asyncinit.SaasConfig',
    'Calculus.Initialisation.AsyncInit.asyncinit',
]
JOBS_ALIAS = {
    # 'Calculus.Maths.Matrix.Multiplication': 'Calculus.Maths.Matrix.MatrixMultiplicationPython',
    'Calculus.Maths.Matrix.Multiplication': 'Calculus.Maths.Matrix.MatrixMultiplicationNumpy',
}

# == END MODULES CONFIG ==

''' Default statics constants from the Config '''

# __STATICS_CONSTANTS__ = { 'varName' : 'Constant Value', 'varName2': 0 }

__STATICS_CONSTANTS__ = {}

__DEFAULT_THREAD__ = 1
__DEFAULT_WORKER_NAME__ = 'MeteorFullServer.MeteorFullServer'

# Not Yep for SHA3
# __HASH__ = 'sha3_256'


#__HASH__ = 'sha256'
# __HASH_RE__ = re.compile('[a-fA-F0-9]{64}')

__HASH__ = 'md5'
__HASH_RE__ = re.compile('[a-fA-F0-9]{32}')


# Config Global const
__GEOCODES_COLLECTIONS__ = ('geocodes',)
__GEOGRAPHICAL_COLLECTIONS__ = ('geographical.corine',
                                'postal2insee',)
__RESIDENTIAL_COLLECTIONS__ = ('demand.residential.surfaces',
                               'demand.residential.propelants',
                               'demand.residential.households',
                               'demand.residential.construction_dates')
__RESIDENTIAL_DYN_COLLECTIONS__ = ('demand.residential.dynres',
                                   'demand.residential.frenchtourists', 'demand.residential.foreigntourists')
__RESIDENTIAL_SEC_COLLECTIONS__ = ('demand.residential.secondary',)
__RESIDENTIAL_TRANSPORT_COLLECTIONS__ = ('demand.transport.infrastructure',
                                         'demand.transport.home_work',)

__EMPLOYEES_COLLECTIONS__ = ('demand.employees',)
__WEATHER_COLLECTIONS__ = ('weather.observations',
                           'weather.stations',
                           'weather.observations.interpolated',
                           'weather.interpolation_matrix',
                           'weather.reconstructed_years',
                           'weather.noise',
                           'weather.reconstructed.interpolation_matrices',
                           'weather.reconstructed_years_numpy',
                           'weather.france.averaged',
                           'weather.france.longterm')
__SUPPLY_COLLECTIONS__ = ('supply.enr',
                          'supply.dispatchable',
                          'supply.ols',
                          'supply.glm',
                          'supply.hydrorun2015',
                          'supply.heatgrid',
                          'supply.coldgrid',
                          'supply.windparksdict')
__POLLUTANTS_COLLECTIONS__ = ('pollutants.inventory',)
__AGRICULTURE_COLLECTIONS__ = ('agriculture.surf.animals',)
MONGODB_REFDATABASE = 'METEOR_ref'
MONGODB_METEOR_DATABASE = 'METEOR'
MONGODB_INIT_DB = 'saasconfig'
__INIT_COLLECTIONS__ = {'main': 'config_async'}
MONGO_ZIP_DB = 'zipfiles'
MONGODB_COLLECTIONS = ('geocodes',)
__ZIP_GRAPHS__ = 'graphs'
__PICKLE_THRESHOLD__ = 15 * 1024 * 1024
__NB_YEARS_WEATHER_PRECALC__ = 10
__NB_DAYS_WEATHER_SMOOTH__ = 2
__NB_PARTS_YEAR__ = 12


# Split in MAP
PROJECTION_SPLIT_LIMIT = 50

# Config Demand/Industry
__IND_EMPL_CONS_PATH__ = 'datas/csv/industry/industry_employees_consumption.csv'
__IND_USE_TYPE_PATH__ = 'datas/csv/industry/industry_use_type.csv'
__IND_SEASONALITY_PATH__ = 'datas/csv/industry/seasonality.csv'
# Config Demand/Tertiary
__TER_EMPL_CONS_PATH__ = 'datas/csv/tertiary/tertiary_employees_consumption.csv'
__TER_LIGHT_CONS_PATH__ = 'datas/csv/tertiary/tertiary_lighting_monthly_charge.csv'
__TERHEAT_EMPL_CONS_PATH__ = 'datas/csv/tertiary/tertiary_heating_employees_consumption.csv'
# Config Demand/Residential
__RES_AIR_USE_CONS_PATH__ = 'datas/csv/residential/airing/use.csv'
__RES_AC_DISTRIB_CONS_PATH__ = 'datas/csv/residential/airconditioning/distribution.csv'
__RES_AC_EFF_CONS_PATH__ = 'datas/csv/residential/airconditioning/efficiency.csv'
__RES_EQ_POSS_CONS_PATH__ = 'datas/csv/residential/equipments/proportions.csv'
__RES_EQ_USE_CONS_PATH__ = 'datas/csv/residential/equipments/standard_charge.csv'
__RES_COOK_POSS_CONS_PATH__ = 'datas/csv/residential/cooking/proportions.csv'
__RES_COOK_USE_CONS_PATH__ = 'datas/csv/residential/cooking/standard_charge.csv'
__RES_LIGHT_MONTHLY_CONS_PATH__ = 'datas/csv/residential/lighting/monthly_charge.csv'
__RES_WH_USE_CONS_PATH__ = 'datas/csv/residential/waterheating/use.csv'
__SECONDARY_RES_PATH__ = 'datas/csv/databases/mongodb/res_secondary.csv'
# Config Demand/Residential/DynamicResidents
__RES_DYNRES__ = ['datas/csv/tourism/dynamic_residents.csv',
                  'datas/csv/tourism/french_tourists.csv', 'datas/csv/tourism/foreign_tourists.csv']

# Config Demand/Transport
__TRANSPORT_PEOPLE_USE_PATH__ = 'datas/csv/transport/use.csv'
__TRANSPORT_ONTHEROAD_PATH__ = 'datas/csv/transport/ontheroad_people.csv'
__TRANSPORT_ONTHEROAD2_PATH__ = 'datas/csv/transport/ontheroad_freight.csv'
__TRANSPORT_PEOPLE_MOBILITY_PATH__ = 'datas/csv/transport/mobility.csv'
__TRANSPORT_FREIGHT_PATH__ = 'datas/csv/transport/freight.csv'
# _calc_hash return random
no_hash_for_calculus = True
# When var name is not defined, hash value to get var name or return a
# random var name string
name_from_hash_value = True
# When calculating hash from method & args, prefers to hash value or the
# has_name of the variables
hash_prefers_value = True
# How many second to wait between jobs and dependency check
sleep_time_for_dependencies = 0.1
#  configuring the memory cleanup parameters
cleanup_coeff_time = 0.5
cleanup_coeff_poids = 0.5
cleanup_threshold_mem = None
#cleanup_threshold_mem = 0.80
# Config for spatial interpolation
__INTERPO_NNEAR__ = 20
__INTERPO_P__ = 2

# Configuration of DefMatrixBuilder

__DEF_MATRIX_BUILDER_CONS_PATH__ = 'datas/csv/default_values/dot.csv'


# Configuration of Deltas for temporal evolution
deltas = [deltaYears, deltaHours]
save_delta = deltaYears
calc_delta = deltaHours
save_inter_delta = []

# Number of calc_delta in a save_del
# For now : number of hour in a year
__NB_CALC_TEMPORAL_STEP__ = NORMAL_YEAR_NHOUR
# len(mois) + len(weeks) + len(year)
# 12        + 52         + 1
__NB_MAP_TEMPORAL_STEP__ = 65
# PerCent for calc calculus

extractParamPerCent = 1
constructIndepVarPerCent = 3
PERCENT_FOR_SUMMARY = 10
PERCENT_FOR_SUMMARY2 = 3

# Max recursif set for get_val
MAX_GETVAL_DEPTH = 10


# Dependance order for calculation of variables(Sector)

sectors_dependances = {
    'Demand_Industry': set(),
    'Demand_Residential': set(),
    'Demand_Tertiary': set(),
    'Demand_Transport': set(),
    'Supply': set(),
}

varnames_dependances = {
    'Demand_Industry': {
        'Demand_Industry_Activity_ProdInd': set(),
        'Demand_Industry_Activity_Lifetime': set(),
        'Demand_Industry_Consumption_Efficiency': {'Demand_Industry_Activity_Activity', },
    },
    'Demand_Residential': {
        'Demand_Residential_Construction_Bbc': set(),
        'Demand_Residential_Construction_Bepos': set(),
        'Demand_Residential_Consumption_Airconditioning': {'Demand_Residential_Construction_Bbc',
                                                           'Demand_Residential_Construction_Bepos',
                                                           'Demand_Residential_Renovation_From00to12',
                                                           'Demand_Residential_Renovation_From45to75',
                                                           'Demand_Residential_Renovation_From75to90',
                                                           'Demand_Residential_Renovation_From90to00',
                                                           'Demand_Residential_Renovation_before45'},
        'Demand_Residential_Consumption_Airing': {'Demand_Residential_Construction_Bbc',
                                                  'Demand_Residential_Construction_Bepos',
                                                  'Demand_Residential_Renovation_From00to12',
                                                  'Demand_Residential_Renovation_From45to75',
                                                  'Demand_Residential_Renovation_From75to90',
                                                  'Demand_Residential_Renovation_From90to00',
                                                  'Demand_Residential_Renovation_before45'},
        'Demand_Residential_Consumption_Equipments': {'Demand_Residential_Construction_Bbc',
                                                      'Demand_Residential_Construction_Bepos',
                                                      'Demand_Residential_Renovation_From00to12',
                                                      'Demand_Residential_Renovation_From45to75',
                                                      'Demand_Residential_Renovation_From75to90',
                                                      'Demand_Residential_Renovation_From90to00',
                                                      'Demand_Residential_Renovation_before45'},
        'Demand_Residential_Consumption_Cooking': {'Demand_Residential_Construction_Bbc',
                                                   'Demand_Residential_Construction_Bepos',
                                                   'Demand_Residential_Renovation_From00to12',
                                                   'Demand_Residential_Renovation_From45to75',
                                                   'Demand_Residential_Renovation_From75to90',
                                                   'Demand_Residential_Renovation_From90to00',
                                                   'Demand_Residential_Renovation_before45'},
        'Demand_Residential_Consumption_Heating': {'Demand_Residential_Construction_Bbc',
                                                   'Demand_Residential_Construction_Bepos',
                                                   'Demand_Residential_Renovation_From00to12',
                                                   'Demand_Residential_Renovation_From45to75',
                                                   'Demand_Residential_Renovation_From75to90',
                                                   'Demand_Residential_Renovation_From90to00',
                                                   'Demand_Residential_Renovation_before45'},
        'Demand_Residential_Consumption_Lighting': {'Demand_Residential_Construction_Bbc',
                                                    'Demand_Residential_Construction_Bepos',
                                                    'Demand_Residential_Renovation_From00to12',
                                                    'Demand_Residential_Renovation_From45to75',
                                                    'Demand_Residential_Renovation_From75to90',
                                                    'Demand_Residential_Renovation_From90to00',
                                                    'Demand_Residential_Renovation_before45'},
        'Demand_Residential_Renovation_From00to12': set(),
        'Demand_Residential_Renovation_From45to75': set(),
        'Demand_Residential_Renovation_From75to90': set(),
        'Demand_Residential_Renovation_From90to00': set(),
        'Demand_Residential_Renovation_before45': set(),
    },
    'Demand_Tertiary': {
        'Demand_Tertiary_Activity_Economy': set(),
        'Demand_Tertiary_Consumption_Airconditioning': {'Demand_Tertiary_Activity_Economy',
                                                        'Demand_Tertiary_Renovation_Thermal'},
        'Demand_Tertiary_Consumption_Heating': {'Demand_Tertiary_Activity_Economy',
                                                'Demand_Tertiary_Renovation_Thermal'},
        'Demand_Tertiary_Consumption_Lighting': {'Demand_Tertiary_Activity_Economy',
                                                 'Demand_Tertiary_Renovation_Thermal'},
        'Demand_Tertiary_Consumption_Specificuse': {'Demand_Tertiary_Activity_Economy',
                                                    'Demand_Tertiary_Renovation_Thermal'},
        'Demand_Tertiary_Renovation_Thermal': set(),
    },
    'Demand_Transport': {
        'Demand_Transport_Freight_Consumption': {'Demand_Transport_Freight_Traffic'},
        'Demand_Transport_Freight_Traffic': set(),
        'Demand_Transport_Infrastructure_Infrastructure': set(),
        'Demand_Transport_People_Consumption': {'Demand_Transport_People_Mobility'},
        'Demand_Transport_People_Mobility': set(),
    },
    'Supply': {
        'Supply_Electricitygrid_Fatal': set(),
    },
}
# list of sectors to be computed at the same time via an aliased sector
simultaneous_sectors = {
    'Supply_Electricitygrid_Coal': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_Gas': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_HydroLake': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_Nuclear': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_Oil': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_Biomass': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_Waste': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_HydroSTEP': 'Supply_Electricitygrid_Dispatchable',
    'Supply_Electricitygrid_HydroRun': 'Supply_Electricitygrid_Fatal_HydroRun',
    'Supply_Electricitygrid_Wind': 'Supply_Electricitygrid_Fatal_Wind',
    'Supply_Electricitygrid_PV': 'Supply_Electricitygrid_Fatal_PV',

}

# List constants and method to calculate the missing constantes

# TODO
constants_method = {
    'varname:order': 'Calculus.Constants.Sectors.MetaSectors',
    'Hypothesis:Default': 'Calculus.Initialisation.Hypothesis.hypo_matrix_from_babel.DefMatrixBuilderConstants',
    'Hypothesis:Default:Ones': 'Calculus.Initialisation.Hypothesis.hypo_matrix_from_babel.DefMatrixBuilderConstants',
    'Hypothesis:Default:Order': 'Calculus.Initialisation.Hypothesis.hypo_matrix_from_babel.DefMatrixBuilderConstants',
    'Hypothesis:Default:Named': 'Calculus.Initialisation.Hypothesis.hypo_matrix_from_babel.DefMatrixBuilderConstants',
    'Hypothesis:Default:Types': 'Calculus.Initialisation.Hypothesis.hypo_matrix_from_babel.DefMatrixBuilderConstants',
    'Hypothesis:Default:Absval': 'Calculus.Initialisation.Hypothesis.hypo_matrix_from_babel.DefMatrixBuilderConstants',
    'geocodes': 'Calculus.Initialisation.LoadingInCache.GeocodeInsee',
    'population': 'Calculus.Initialisation.LoadingInCache.GeocodeInsee',
    'roughness': 'Calculus.Initialisation.LoadingInCache.Roughness',
    'surface': 'Calculus.Initialisation.LoadingInCache.GeocodeInsee',
    'position': 'Calculus.Initialisation.LoadingInCache.GeocodeInsee',
    'geocodes_indexes': 'Calculus.Initialisation.LoadingInCache.GeocodeInsee',
    'counties': 'Calculus.Initialisation.LoadingInCache.Counties',
    'counties_indexes': 'Calculus.Initialisation.LoadingInCache.CountiesIndexes',
    'dynres': 'Calculus.Initialisation.LoadingInCache.DynamicResidential',
    'french_tourists': 'Calculus.Initialisation.LoadingInCache.FrenchTourists',
    'foreign_tourists': 'Calculus.Initialisation.LoadingInCache.ForeignTourists',
    'weather:variables': 'Calculus.Constants.Weather.WeatherConstants',
    'weather:stations': 'Calculus.Constants.Weather.WeatherConstants',
    'postal2insee': 'Calculus.Initialisation.Demand.demand.Postal2Insee',
    'insee2postal': 'Calculus.Initialisation.Demand.demand.Insee2Postal',
    'heatgrid_loc': 'Calculus.Supply.Heatgrid.heatgrid.Localisation',
    'counties_to_regions': 'Calculus.Initialisation.LoadingInCache.CountiesToRegions',
    'reg_ind_frac_fromeider': 'Calculus.Initialisation.LoadingInCache.RegionIndustryFraction',
    'reg_ind_frac_fromconso': 'Calculus.Initialisation.LoadingInCache.RegionIndustryFromEmployees',
    'agri_firms': 'Calculus.Demand.Agriculture.IniEnd.IniAgri.IniAgri',
    'agri_workers': 'Calculus.Demand.Agriculture.IniEnd.IniAgri.IniAgri',
    'agri_surf': 'Calculus.Demand.Agriculture.IniEnd.IniAgri.IniAgri',
    'agri_animals': 'Calculus.Demand.Agriculture.IniEnd.IniAgri.IniAgri',
    'agri_surf_abs': 'Calculus.Demand.Agriculture.IniEnd.IniAgri.IniAgri',
    'agri_animals_abs': 'Calculus.Demand.Agriculture.IniEnd.IniAgri.IniAgri',
    'corine_raw': 'Calculus.Initialisation.LoadingInCache.Roughness',
    'TempLT': 'Calculus.Weather.DistribLongTerm.TempLT',
    'TempRawLT': 'Calculus.Weather.DistribLongTerm.TempRawLT',
    'deghourlt': 'Calculus.Weather.DistribLongTerm.DegreeHourLT',
    'n_train_station': 'Calculus.Demand.Transport.IniEndCalculations.Infra.NInfra',
    'n_airport': 'Calculus.Demand.Transport.IniEndCalculations.Infra.NInfra',
    'n_parking': 'Calculus.Demand.Transport.IniEndCalculations.Infra.NInfra',
    'km_road': 'Calculus.Demand.Transport.IniEndCalculations.Infra.NInfra',
    'km_highway': 'Calculus.Demand.Transport.IniEndCalculations.Infra.NInfra',
    'ontheroadfullp': 'Calculus.Demand.Transport.IniEndCalculations.People.Ontheroad',
    'ontheroadfullf': 'Calculus.Demand.Transport.IniEndCalculations.Freight.Ontheroad',

    # 1 # Demand

    # 1.1 # Residential

    # 1.1.1 # Commons
    'Demand:NewConstruction:Shares:Ini': 'Calculus.Demand.Residential.Construction.BBCBeposSharesIni',
    'Demand:Residential:SqrtMeanSurfacesByRoom': 'Calculus.Initialisation.Demand.demand.ResidentialConstants',
    'Demand:Residential:SurfacesByConstrDate': 'Calculus.Initialisation.Demand.demand.ResidentialConstants',
    'Demand:Residential:TotConstr:Ini': 'Calculus.Demand.Residential.Construction.TotalConstrIni',
    'Demand:Residential:NewConstr:Ini': 'Calculus.Demand.Residential.Construction.ConstrIni',
    'Demand:Residential:LegConstr:Ini': 'Calculus.Demand.Residential.Construction.LegConstrIni',
    'Demand:Residential:Construction_dates': 'Calculus.Initialisation.Demand.demand.ResidentialConstants',
    'Demand:Residential:Surfaces': 'Calculus.Initialisation.Demand.demand.ResidentialConstants',
    'Demand:Residential:Propelants': 'Calculus.Initialisation.Demand.demand.ResidentialConstants',
    'Demand:Residential:Households': 'Calculus.Initialisation.Demand.demand.ResidentialConstants',
    'Demand:Residential:Renovation:Start_R': 'Calculus.Demand.Residential.Renovation.RenovationStartR',
    'Demand:Residential:R_coef_new_constr': 'Calculus.Demand.Residential.Renovation.R_coef_new_constr',
    'Demand:Residential:DPERaw': 'Calculus.Initialisation.Demand.demand.MatricesDPE',
    'Demand:Residential:DPEDistrib': 'Calculus.Demand.Residential.Renovation.DPEdistrib',
    'Demand:Residential:Secondary': 'Calculus.Initialisation.Demand.demand.ResidentialSecondaryConstants',

    # 1.1.2 # Airconditionning
    'Demand:Residential:Airconditioning:Distribution:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Airconditioning.ACIni',
    'Demand:Residential:Airconditioning:Distribution': 'Calculus.Demand.Residential.IniEndCalculations.Airconditioning.Distribution',
    'Demand:Residential:Airconditioning:Pac:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Airconditioning.ACTechnoIni',
    'Demand:Residential:Airconditioning:Basic:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Airconditioning.ACTechnoIni',
    # 1.1.3 # Airing
    'Demand:Residential:Airing:Simple:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Airing.SimpleIni',
    'Demand:Residential:Airing:Double:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Airing.DoubleIni',
    'Demand:Residential:Airing:Use': 'Calculus.Demand.Residential.IniEndCalculations.Airing.Use',
    # 1.1.4 # Equipments
    'Demand:Residential:Equipments:Possession': 'Calculus.Demand.Residential.IniEndCalculations.Equipments.Possession',
    'Demand:Residential:Equipments:Use': 'Calculus.Demand.Residential.IniEndCalculations.Equipments.Use',
    'Demand:Residential:Equipments:Distribution:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Equipments.PossessionIni',
    'Demand:Residential:Equipments:Nominal:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Equipments.NominalIni',
    # 1.1.4 # Cooking



    'Demand:Residential:Cooking:Possession': 'Calculus.Demand.Residential.IniEndCalculations.Cooking.Possession',
    'Demand:Residential:Cooking:Use': 'Calculus.Demand.Residential.IniEndCalculations.Cooking.Use',
    'Demand:Residential:Cooking:Distribution:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Cooking.PossessionIni',
    'Demand:Residential:Cooking:Nominal:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Cooking.NominalIni',
    # 1.1.5 # Heating
    'Demand:Residential:Heating:PropelantsPercent': 'Calculus.Demand.Residential.IniEndCalculations.Heating.PropelantsPercent',
    'Demand:Residential:Heating:Propelant:Distribution:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Heating.HeatDistribIni',
    'Demand:Residential:Heating:Propelant:Techno:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Heating.HeatTechnoIni',
    # 1.1.6 # Lighting
    'Demand:Residential:Lighting:Incandescent:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.IncIni',
    'Demand:Residential:Lighting:Lfc:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.LfcIni',
    'Demand:Residential:Lighting:Led:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.LedIni',
    'Demand:Residential:Lighting:MonthlyUse': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.MonthlyUse',
    'Demand:Residential:Lighting:MonthlyUse1997': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.MonthlyUse',
    'Demand:Residential:Lighting:RefLum': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.RefLum',
    'Demand:Residential:Lighting:Luminosity:Response': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.ResponseLighting',
    'Demand:Residential:Lighting:Luminosity:Coeffs': 'Calculus.Demand.Residential.IniEndCalculations.Lighting.CoeffsLighting',
    # 1.1.7 # Waterheating
    'Demand:Residential:Waterheating:Basic:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Waterheating.BasicIni',
    'Demand:Residential:Waterheating:Superisolated:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Waterheating.SuperisolatedIni',
    'Demand:Residential:Waterheating:Thermodynamic:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Waterheating.ThermodynamicIni',
    'Demand:Residential:Waterheating:Solar:Ini': 'Calculus.Demand.Residential.IniEndCalculations.Waterheating.SolarIni',
    'Demand:Residential:Waterheating:Use': 'Calculus.Demand.Residential.IniEndCalculations.Waterheating.Use',

    # 1.2 # Industry

    # 1.2.1 # Commons
    'Demand:Industry:Seasonality': 'Calculus.Demand.Industry.IniEndCalculations.ProdInd.Seasonality',
    'Demand:Industry:Employees:Ini': 'Calculus.Demand.Industry.IniEndCalculations.Employees.EmployeesIni',
    'Demand:Industry:EmployeesConsumptions': 'Calculus.Demand.Industry.IniEndCalculations.Employees.EmployeesConsumption',
    'Demand:Industry:EmployeesConsumptionsRenorm': 'Calculus.Demand.Industry.IniEndCalculations.Employees.EmployeesConsumption',
    'Demand:Industry:Activity:Ini': 'Calculus.Demand.Industry.IniEndCalculations.Employees.IndActivityIni',
    'Demand:Industry:UseType': 'Calculus.Demand.Industry.IniEndCalculations.Efficiency.UseType',
    # 1.2.2 # Efficiency
    'Demand:Industry:Efficiency:Processes:Ini': 'Calculus.Demand.Industry.IniEndCalculations.Efficiency.ProcessesIni',
    'Demand:Industry:Efficiency:Motors:Ini': 'Calculus.Demand.Industry.IniEndCalculations.Efficiency.MotorsIni',
    'Demand:Industry:Efficiency:Heating:Ini': 'Calculus.Demand.Industry.IniEndCalculations.Efficiency.HeatingIni',
    'Demand:Industry:Efficiency:Other:Ini': 'Calculus.Demand.Industry.IniEndCalculations.Efficiency.OtherIni',
    # 1.2.3 # ProdInd
    # 1.2.4 # Lifetime

    # 1.3 # Tertiary

    # 1.3.1 # Commons
    'Demand:Tertiary:Employees:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Employees.EmployeesIni',
    'Demand:Tertiary:Surfaces:Ini': 'Calculus.Demand.Tertiary.Construction.SurfacesIni',
    'Demand:Tertiary:Employees:WS:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Employees.EmployeesWSCateg',
    # 1.3.2 # Airconditionning
    'Demand:Tertiary:Airconditioning:Basic:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Airconditioning.ACTechnoIni',
    'Demand:Tertiary:Airconditioning:Pac:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Airconditioning.ACTechnoIni',
    'Demand:Tertiary:ACSurfaces:Ini': 'Calculus.Demand.Tertiary.Construction.ACSurfacesIni',
    'Demand:Tertiary:ACFrac:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Airconditioning.PercentAC',
    # 1.3.3 # Heating
    'Demand:Tertiary:Heating:Propelant:Distribution:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Heating.PropDistribIni',
    'Demand:Tertiary:HeatSurfaces:Ini': 'Calculus.Demand.Tertiary.Construction.HeatSurfacesIni',
    'Demand:Tertiary:PctHeat:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Heating.PercentHeated',
    # 1.3.4 # Lighting
    'Demand:Tertiary:Lighting:MonthlyCharge': 'Calculus.Demand.Tertiary.IniEndCalculations.Lighting.MonthlyCharge',
    'Demand:Tertiary:Lighting:Incandescent:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Lighting.IncIni',
    'Demand:Tertiary:Lighting:Lfc:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Lighting.LfcIni',
    'Demand:Tertiary:Lighting:Led:Ini': 'Calculus.Demand.Tertiary.IniEndCalculations.Lighting.LedIni',
    # 1.3.5 # SpecificUse
    'Demand:Tertiary:SpecUse:HourChargeConsumptions': 'Calculus.Demand.Tertiary.IniEndCalculations.Specificuse.SpecificuseIni',

    # 1.4 # Transport

    # 1.4.1 # People
    'transport_infrastructure': 'Calculus.Demand.Transport.IniEndCalculations.Infra.InfraIni',
    'Demand:Transport:People:Mobility:Ini': 'Calculus.Demand.Transport.IniEndCalculations.People.MobilityIni',
    'Demand:Transport:People:Efficiency:Ini': 'Calculus.Demand.Transport.IniEndCalculations.People.EfficiencyIni',
    'Demand:Transport:People:Use': 'Calculus.Demand.Transport.IniEndCalculations.People.Use',
    # 1.4.2 # Freight
    'Demand:Transport:Freight:Efficiency:Ini': 'Calculus.Demand.Transport.IniEndCalculations.Freight.EfficiencyIni',
    'Demand:Transport:Freight:Traffic:Ini': 'Calculus.Demand.Transport.IniEndCalculations.Freight.TrafficIni',
    # 1.4.3 # Infrastructure
    'Demand:Transport:Infrastructure:Ini': 'Calculus.Demand.Transport.IniEndCalculations.Infra.InfraIni',

    # 2 # Supply
    # 2.1 # Fatal Prod
    'Supply:Wind:Turbines:Distribution:Ini': 'Calculus.Supply.Electricitygrid.IniEnd.EnRDistribIni',
    'Supply:Wind:Turbines:Carac:Ini': 'Calculus.Supply.Electricitygrid.IniEnd.WindCaracIni',
    'Supply:Solar:PV:Distribution:Ini': 'Calculus.Supply.Electricitygrid.IniEnd.EnRDistribIni',
    'Supply:Dispatchable:Distribution:Ini': 'Calculus.Supply.Electricitygrid.IniEnd.DispatchableDistribIni',
    'Supply:HydroRun:Distrib:Ini': 'Calculus.Supply.Electricitygrid.IniEnd.HydroRunDistribIni',
    'Supply:HydroRun:Distrib:Ini:Raw': 'Calculus.Supply.Electricitygrid.IniEnd.EnRDistribIni',
    'Supply:Dispatchable:OLS': 'Calculus.Supply.Electricitygrid.IniEnd.DispatchableOLS',
    'Supply:Dispatchable:GLM': 'Calculus.Supply.Electricitygrid.IniEnd.DispatchableGLM',
    'Supply:HydroRun:Base:Prod': 'Calculus.Supply.Electricitygrid.IniEnd.BaseHydroProd',
    'Supply:HydroRun:Base:Noise': 'Calculus.Supply.Electricitygrid.IniEnd.BaseHydroNoise',
    'Supply:Heatgrid:Propelant:Distrib:Ini': 'Calculus.Supply.Heatgrid.iniheatgrid.HeatgridPropDistribIni',
    'Supply:Heatgrid:Neighbours:Dispatch': 'Calculus.Supply.Heatgrid.iniheatgrid.HeatgridPropDistribIni',
    'Supply:Heatgrid:Propelant:Losses:Ini': 'Calculus.Supply.Heatgrid.iniheatgrid.HeatgridPropDistribIni',

    # 3 # Weather
    'Wind:Longterm:20160:mean': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',


    'Wind:Longterm:20160:std': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',
    'Wind:Longterm:10:mean': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',
    'Wind:Longterm:10:std': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',
    'Wind:Longterm:10:distrib': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',
    'Wind:Longterm:10:xaxis': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',
    'Lum:Longterm:10:mean': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',
    'Lum:Longterm:10:std': 'Calculus.Initialisation.LoadingInCache.WeatherLongTerm',
}

non_config_sectors_required = []
non_config_sectors = ['Global_Weather', 'Demand_Agriculture_Animals', 'Demand_Agriculture_Plants']
depend_post_first = ['Calculus.Demand.Residential.Secondary']

abs_val_method = {
    'Supply_Electricitygrid_Fatal_Wind:All_power_wind_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.WindDistribMask',
    'Supply_Electricitygrid_Fatal_PV:All_power_pv_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.PVDistribMask',
    'Supply_Electricitygrid_Fatal_HydroRun:All_power_hydrorun_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.HydroRunDistribMask',
    'Supply_Electricitygrid_Dispatchable_Nuclear:All_power_nuc_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Supply_Electricitygrid_Dispatchable_Oil:All_power_oil_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Supply_Electricitygrid_Dispatchable_Gas:All_power_gas_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Supply_Electricitygrid_Dispatchable_Coal:All_power_coal_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Supply_Electricitygrid_Dispatchable_HydroLake:All_power_hydrolake_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Supply_Electricitygrid_Dispatchable_HydroSTEP:All_power_hydrostep_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Supply_Electricitygrid_Dispatchable_Waste:All_power_waste_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Supply_Electricitygrid_Dispatchable_Biomass:All_power_biomass_powerchangemw': 'Calculus.Initialisation.Hypothesis.supply.DispatchableDistribMask',
    'Demand_Agriculture_Animals_Number:All_agrianimals_animalsnumber': 'Calculus.Initialisation.Hypothesis.demand.AnimalsNumber',
    'Demand_Agriculture_Plants_Surface:All_agriplants_plantsurf': 'Calculus.Initialisation.Hypothesis.demand.PlantsSurface',
    'Demand_Industry_Activity_Activity:CM_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CD_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CJ_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CA_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CK_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CL_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CG_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CI_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CE_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CB_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CF_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:BZ_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CH_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:CC_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:EZ_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Industry_Activity_Activity:FZ_nb_empl_nb_empl': 'Calculus.Initialisation.Hypothesis.demand.EmployeesInd',
    'Demand_Transport_Infrastructure_Infrastructure:All_infrastructure_airport': 'Calculus.Initialisation.Hypothesis.demand.Nairport',
    'Demand_Transport_Infrastructure_Infrastructure:All_infrastructure_trainstation': 'Calculus.Initialisation.Hypothesis.demand.Ntrain',
    'Demand_Transport_Infrastructure_Infrastructure:All_infrastructure_parking': 'Calculus.Initialisation.Hypothesis.demand.Nparking',
    'Demand_Transport_Infrastructure_Infrastructure:All_infrastructure_highway': 'Calculus.Initialisation.Hypothesis.demand.KMhighway',
    'Demand_Transport_Infrastructure_Infrastructure:All_infrastructure_road': 'Calculus.Initialisation.Hypothesis.demand.KMroad',
    'Demand_Transport_Infrastructure_Infrastructure:All_infrastructure_bikeroad': 'Calculus.Initialisation.Hypothesis.demand.Nbikeroad',
}

constants_method.update(abs_val_method)

# Number of time a meteor server should see a job before worry about it
MAX_JOB_RESENT = 10

# Summary

GLOBAL_ENERGY_SUMMARY = {'Summary_Global_Energysummary_energytotaltime': None,
                         'Summary_Global_Energysummary_energytotalmap': None}
GLOBAL_GES_SUMMARY = {'Summary_Global_Gessummary_gestotal': None}
