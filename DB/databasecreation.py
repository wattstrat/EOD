

from Inputs.Csv.Demand.Insee.Surfaces.surfaces_csv import SurfacesCsv
from Inputs.Csv.Meteor.GeocodesInfos.geocodes_infos import GeocodesInfos
from Inputs.Csv.Demand.Insee.Propelants.propelants_csv import PropelantsCsv
from Inputs.Csv.Demand.Insee.Secondary.secondary import SecondaryCsv
from Inputs.Csv.Demand.Insee.Households.households_csv import HouseholdsCsv
from Inputs.Csv.Demand.Transport.infrastructure import InfrastructureCsv
from Inputs.Csv.Demand.Transport.home_work import HomeWorkCsv
from Inputs.Csv.Demand.Employees.employees import EmployeesCsv
from Inputs.Csv.Demand.Insee.ConstructionDates.construction_dates_csv import ConstructionDatesCsv
from Inputs.Csv.Supply.Heatgrid import Heatgrid
from Inputs.Csv.Pollutants.inventory import Inventory
from Inputs.Crawlers.Weather.Meteociel.Forecasts.forecasts import Forecasts
from Inputs.Crawlers.Weather.Meteociel.Observations.observations import Observations as MObservations
from Inputs.Crawlers.Weather.Wunderground.Observations.observations import Observations as WObservations
from Inputs.DB.Interpolate.interpolate import InterpolateWeather
from Inputs.DB.InterpolationMatrix.interpolation_matrix import InterpolationMatrix
from Inputs.DB.Nin.nin import DBNin
from Inputs.DB.NoiseWeather.noise_weather import NoiseWeather
from Inputs.DB.WeatherScenarPool.weather_scenario_pool import WeatherScenarPool
from Inputs.Csv.Meteor.Weather.StationsInfos.stations_infos import StationsInfos
from Inputs.Csv.Demand.Tourism.dynres import Dynres
from Inputs.Csv.Supply.EnR import EnR
from Inputs.Computations.OLSSupply.olssupply import OLSSupply
from Inputs.Csv.Supply.Dispatchable import DispatchableInstall
from Inputs.Csv.Supply.HydroRun import HydroRun
from Inputs.Csv.Meteor.Corine.corine import CorineCsv
from Inputs.DB.Uniformize.uniform_residential import DBUniformRes
from Inputs.Computations.GlobalWeather.weather import OneWeather, LongTermWeather
from Inputs.Csv.Demand.Insee.Postal.postal import Postal2Insee
from Inputs.Csv.WeatherMeteoCiel.weather_meteociel import StationIntersection
from Inputs.Csv.WeatherMeteoCiel.weather_meteociel import SolarIrradiance
from Inputs.Xlsx.Agriculture.agriculture import AgricultureStructure
from Inputs.Csv.Supply.WindParks import ParksBuilder

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


class DatabaseCreation(object):

    def __init__(self, *args, **kwargs):
        self.run(*args, **kwargs)

    def create_db_geocodes(self):
        try:
            if __debug__:
                logger.debug('Creating collection geocodes')
            GeocodesInfos()
        except:
            if __debug__:
                logger.error('Geocodes DB creation error')
            raise

    def create_db_residential(self):
        try:
            if __debug__:
                logger.debug('Creating collections residential')
            if __debug__:
                logger.debug('Creating collection surfaces')
            SurfacesCsv()
            if __debug__:
                logger.debug('Creating collection propelants')
            PropelantsCsv()
            if __debug__:
                logger.debug('Creating collection households')
            HouseholdsCsv()
            if __debug__:
                logger.debug('Creating collection constuction_dates')
            ConstructionDatesCsv()
        except:
            if __debug__:
                logger.error('Residential DB creation error')
            raise

    def create_db_residential_secondary(self):
        try:
            if __debug__:
                logger.debug('Creating collection secondary_residential')
            SecondaryCsv()
        except:
            if __debug__:
                logger.error('Residential DB creation error')
            raise

    def create_db_transport(self):
        try:
            if __debug__:
                logger.debug('Creating collection transport')
            InfrastructureCsv()
            HomeWorkCsv()
        except:
            if __debug__:
                logger.error('Transport DB creation error')
            raise

    def create_db_employees(self):
        try:
            if __debug__:
                logger.debug('Creating collection employees')
            EmployeesCsv()
        except:
            if __debug__:
                logger.error('Employees DB creation error')
            raise

    def create_db_heatgrid(self):
        try:
            if __debug__:
                logger.debug(
                    'Creating collection heatgrid localization and percentage of production types')
            Heatgrid()
        except:
            if __debug__:
                logger.error('Heatgrid DB creation error')
            raise

    def create_db_pollutants_inventory(self):
        try:
            if __debug__:
                logger.debug(
                    'Creating collection of pollutants inventory')
            Inventory()
        except:
            if __debug__:
                logger.error('pollutants inventory DB creation error')
            raise

    def create_db_weather_stations(self):
        try:
            if __debug__:
                logger.debug('Creating collection stations infos')
            StationsInfos()
        except:
            if __debug__:
                logger.error('Weather DB creation error')
            raise

    def create_db_weather_interpolation_matrix(self):
        try:
            if __debug__:
                logger.debug('Creating collection interpolation matrix')
            InterpolationMatrix()
        except:
            if __debug__:
                logger.error('Weather DB creation error')
            raise

    def create_db_interpolate(self):
        try:
            if __debug__:
                logger.debug('Creating collection interpolated weather DB')
            InterpolateWeather()
        except:
            if __debug__:
                logger.error('Interpolated weather DB creation error')
            raise

    def create_db_nin(self):
        try:
            if __debug__:
                logger.debug('Creating new DB and nin geocodes')
            DBNin()
        except:
            if __debug__:
                logger.error('DB Nin error')
            raise

    def create_db_weather_reconstructed(self):
        try:
            if __debug__:
                logger.debug('Creating collection reconstructed_years')
            WeatherScenarPool()
        except:
            if __debug__:
                logger.error('Reconstructed years DB error')
            raise

    def create_db_weather_noise(self):
        try:
            if __debug__:
                logger.debug('Creating collection weather_noise')
            NoiseWeather()
        except:
            if __debug__:
                logger.error('Weather noise DB error')
            raise

    def create_db_dynres(self):
        try:
            if __debug__:
                logger.debug('Creating collection dynamic_residential')
            Dynres()
        except:
            if __debug__:
                logger.error('Dynamic residential DB error')
            raise

    def create_db_weather_meteociel(self):
        try:
            if __debug__:
                logger.debug('Creating collection weather.observations')
            meteociel = StationIntersection()
            meteociel.build_documents()
        except:
            if __debug__:
                logger.error('Dynamic residential DB error')
            raise

    def create_db_lum(self):
        try:
            if __debug__:
                logger.debug('Creating collection weather.observations')
            solar = SolarIrradiance()
            solar.build_from_ref()
        except:
            if __debug__:
                logger.error('Dynamic residential DB error')
            raise

    def create_db_all_database(self):
        self.create_db_geocodes()
        self.create_db_residential()
        self.create_db_residential_secondary()
        self.create_db_employees()
        self.create_db_transport()
        self.create_db_employees()
        self.create_db_heatgrid()
        self.create_db_weather_meteociel()
        self.create_db_weather_stations()
        self.create_db_all_from_interpolate()

    def create_db_all_from_interpolate(self):
        self.create_db_interpolate()
        self.create_db_lum()
        self.create_db_nin()
        self.create_db_pollutants_inventory()
        self.create_db_weather_interpolation_matrix()
        self.create_db_weather_reconstructed()
        self.create_db_weather_noise()
        self.create_db_dynres()
        self.create_db_enr()
        self.create_db_dispatchable()
        self.create_db_olssupply()
        self.create_db_corine_landcover()
        self.update_db_uniform_residential()
        self.update_db_france_weather()
        self.update_db_insee2postal()
        self.update_db_agri()

    def create_db_olssupply(self):
        try:
            if __debug__:
                logger.debug('Creating collection for OLSSupply')
            olss = OLSSupply()
            olss.build_ols_coeffs()
            olss.build_glm_coeffs()
        except:
            if __debug__:
                logger.error('OLSSupply DB creation error')
            raise

    def create_db_dispatchable(self):
        try:
            if __debug__:
                logger.debug('Creating collection for Dispatchable')
            DispatchableInstall()
        except:
            if __debug__:
                logger.error('Dispatchable DB creation error')
            raise

    def create_db_enr(self):
        if __debug__:
            logger.debug('Creating enr collection')
        EnR()
        HydroRun()

    def create_db_corine_landcover(self):
        if __debug__:
            logger.debug('Creating corine land cover collection')
        corine = CorineCsv()
        corine.update_database()

    def update_db_uniform_residential(self):
        if __debug__:
            logger.debug('Creating corine land cover collection')
        unif_res = DBUniformRes()
        unif_res.run()

    def update_db_france_weather(self):
        if __debug__:
            logger.debug('Creating france weather collection')
        oneweather = OneWeather()
        oneweather.run()
        longterm = LongTermWeather()
        longterm.run()
        parks = ParksBuilder()
        parks.save_updated_geocodes_dict()

    def update_db_insee2postal(self):
        if __debug__:
            logger.debug('Creating insee2postal collection')
        insee2postal = Postal2Insee()

    def update_db_agri(self):
        if __debug__:
            logger.debug('Creating agriculture collection')
        agri = AgricultureStructure()
        agri.update_database()

    def run(self, parsed):
        if parsed['all']:
            self.create_db_all_database()
        else:
            if parsed['geocodes']:
                self.create_db_geocodes()
            if parsed['residential']:
                self.create_db_residential()
            if parsed['residential_secondary']:
                self.create_db_residential_secondary()
            if parsed['employees']:
                self.create_db_employees()
            if parsed['transport']:
                self.create_db_transport()
            if parsed['employees']:
                self.create_db_employees()
            if parsed['heatgrid']:
                self.create_db_heatgrid()
            if parsed['weather_stations']:
                self.create_db_weather_stations()
            if parsed['nin']:
                self.create_db_nin()
            if parsed['pollutants']:
                self.create_db_pollutants_inventory()
            if parsed['weather_interpolate']:
                self.create_db_interpolate()
            if parsed['all_from_interpolate']:
                self.create_db_all_from_interpolate()
            if parsed['weather_interpolation_matrix']:
                self.create_db_weather_interpolation_matrix()
            if parsed['weather_reconstructed']:
                self.create_db_weather_reconstructed()
            if parsed['weather_noise']:
                self.create_db_weather_noise()
            if parsed['dynres']:
                self.create_db_dynres()
            if parsed['enr']:
                self.create_db_enr()
            if parsed['dispatchable']:
                self.create_db_dispatchable()
            if parsed['olssupply']:
                self.create_db_olssupply()
            if parsed['corine']:
                self.create_db_corine_landcover()
            if parsed['uniformize_res']:
                self.update_db_uniform_residential()
            if parsed['france_average_weather']:
                self.update_db_france_weather()
            if parsed['insee2postal']:
                self.update_db_insee2postal()
            if parsed['meteociel_data']:
                self.update_db_weather_meteociel()
            if parsed['lum_data']:
                self.update_db_lum()
            if parsed['agriculture']:
                self.update_db_agri()


class DatabaseFromCrawler(object):

    def __init__(self, *args, **kwargs):
        self.run(*args, **kwargs)

    def create_meteociel_forecast(self, parsed):
        try:
            if __debug__:
                logger.debug('Creating DB_meteociel_forecast')
            Forecasts(parsed=parsed)
        except:
            if __debug__:
                logger.error('Meteociel forecast DB creation error')
            raise

    def create_meteociel_obs(self, parsed):
        try:
            if __debug__:
                logger.debug('Creating DB_meteociel_observations')
            MObservations(parsed=parsed)
        except:
            if __debug__:
                logger.error('Meteociel observation DB creation error')
            raise

    def create_wunderground_obs(self, parsed):
        try:
            if __debug__:
                logger.debug('Creating DB_wunderground_observations')
            WObservations(parsed=parsed)
        except:
            if __debug__:
                logger.error('Wunderground observations DB creation error')
            raise

    def run(self, parsed):
        if parsed['meteociel_forecast']:
            self.create_meteociel_forecast(parsed)
        if parsed['meteociel_observations']:
            self.create_meteociel_obs(parsed)
        if parsed['wunderground_observations']:
            self.create_wunderground_obs(parsed)
