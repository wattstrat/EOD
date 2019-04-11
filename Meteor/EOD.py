import argparse

from Calculus.EOD.eod import EOD

if __debug__:
    import logging
    logger = logging.getLogger(__name__)

def launch(args, others):
    startEOD = EOD()
    startEOD._run()


def parser(parent_parser):
    parser = parent_parser.add_parser('eod', help='eod command help', aliases=['e'])
    # Set action of the script
    parser.set_defaults(action=launch)
    return parser
