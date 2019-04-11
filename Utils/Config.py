import ast
import Config.variables as variables

if __debug__:
    import logging
    logger = logging.getLogger(__name__)


def update_conf(cmdline, section):
    for var in variables.config[section]:
        try:
            conf = variables.configfile[section]
        except KeyError:
            conf = None
        if var in cmdline:
            ret = cmdline[var]
        elif conf is not None and var in conf:
            ret = ast.literal_eval(conf[var])
        else:
            continue

        if not isinstance(ret, type(variables.config[section][var])):
            if __debug__:
                logger.warning("type of param %s differ : (default) %s / (input) %s. Not changing value",
                               var,  type(variables.config[section][var]), type(ret))
            pass
        else:
            variables.config[section][var] = ret
