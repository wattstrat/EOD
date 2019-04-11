import argparse

from configparser import ConfigParser, ExtendedInterpolation
import os
import sys
import copy
from redis import StrictRedis

from Data.Hypervisor.Politics.RamDBCalculusPolitic import RamDBCalculusPolitic
from DB.Mongo.Mongo import Mongo
import Config.config as config
import Config.variables as variables
from Config.configfile import defaultconfig

from Global.Global import GlobalREFiltered, Global
from Utils.MultiThread import LockProxy

from Utils.Config import update_conf
from Data.RAM.SharedRAM import VariablesSharedRAM

if __debug__:
    import logging
    import logging.config
    logger = logging.getLogger(__name__)


# Configure common argument
def trait_common_args(args):
    parser = ConfigParser(interpolation=ExtendedInterpolation())

    variables.configfile = parser
    variables.config = copy.deepcopy(defaultconfig)

    if args.version:
        print(config.version)
        sys.exit(0)

    # Read actual config file
    parser.read(args.config)
    variables.configfile = parser

    arg = vars(args)

    update_conf(arg, "common")

    if __debug__:
        logconf = variables.config["common"]['logconfigfile']
        if os.path.isfile(logconf):
            logging.config.fileConfig(logconf, disable_existing_loggers=False)

    variables.loader = Global(alias=config.LOADER_ALIAS)

    # Update mongoDB settings
    config.MONGO_SERVER_ADDRESS = variables.config["common"]["mongo_host"]
    config.MONGO_SERVER_PORT = variables.config["common"]["mongo_port"]


    kwargs = {'DB-opt': {'database': 'mytest', 'collection': 'default'}}
    variables.cache = RamDBCalculusPolitic(**kwargs)
    # variables.cache = DataCalculusPolitic(cache)
    kwargs_mongo = {'database': config.MONGODB_METEOR_DATABASE, 'collection': config.__GEOCODES_COLLECTIONS__[0], }
    kwargs_mongo.update({'server_address':'192.168.1.24'})
    # kwargs_mongo.update({'server_address':'localhost', 'server_port':3333})
    variables.mongo = Mongo(**kwargs_mongo)

    variables.calculs = GlobalREFiltered(alias=config.CALCULUS_ALIAS, filters=config.CALCULUS_MODULES)
    # Permit to have calulus wrapped in jobs but calculus alias also inside the Wrapped Job
    variables.jobs_calculs = GlobalREFiltered(alias=config.JOBSCALCULUS_ALIAS, filters=config.JOBSCALCULUS_MODULES)

    # Write current PID
    write_pid()


def write_pid():
    pid = os.getpid()
    try:
        with open(variables.config["common"]["pidfile"], 'w') as pidfile:
            pidfile.write("%d" % (pid))
    except Exception as e:
        # TODO : more specific for execption
        if __debug__:
            logger.warning("[%d] Could not write PID file (%s) : %s", pid, variables.config["common"]["pidfile"], e)
        pass


def describe(args, others):
    print(config.version)
    # For test
    print(variables.config)
    print(others)


def parser(argsparser):
    argsparser.add_argument('--loglevel', type=int, help='set log level')
    argsparser.add_argument('--logconfigfile', type=str, help='set log config file')
    argsparser.add_argument('--config', type=str, default="/etc/meteor/meteor.conf", help='config file')
    argsparser.add_argument('--version', action='store_true', default=False, help='display version')
    argsparser.add_argument('--pidfile', type=str, help='Set PID-file')

    argsparser.add_argument('--mongo-port', type=int, help='Port of the mongodb server')
    argsparser.add_argument('--mongo-host', type=str, help='Host of the mongodb server')
    argsparser.add_argument('--mongo-db', type=str, help='Working database for METEOR')

    argsparser.add_argument('--redis-host', type=str, help='Change value of the redis host')
    argsparser.add_argument('--redis-port', type=int, help='Change value of the redis port')

    argsparser.add_argument('--cache', type=str, help='Class of cache')
    argsparser.add_argument('--cache-opt', type=str, help='Option for the cache')

    argsparser.set_defaults(action=describe)
