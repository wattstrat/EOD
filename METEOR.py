#!/usr/bin/env python3

import argparse
import sys

import Config.config
from Meteor.Common import trait_common_args, parser as pcommon, describe
from Meteor.EOD import parser as pe

# TODO:
#       + PID-file

# Main Parser with option common to all project
parser = argparse.ArgumentParser(prog='METEOR', argument_default=argparse.SUPPRESS)
pcommon(parser)

# Sub-parser section
subparsers = parser.add_subparsers(help='sub-command help')
# get EOD sub command
pe(subparsers)


if __name__ == '__main__':
    """ METEOR entry point. """
    # Remove prog name
    rest = sys.argv[1::]
    args = argparse.Namespace()
    common = False
    # Do all chaining sub command
    if not rest:
        describe(args, [])
        sys.exit(0)

    while rest:
        args, nrest = parser.parse_known_args(rest, namespace=args)
        if common and nrest == rest:
            break
        if not common:
            trait_common_args(args)
            common = True
        if rest and rest[0] == '--':
            # end of parsing, append rest to action
            args.action(args, rest[1::])
            break
        else:
            args.action(args, [])
        rest = nrest

    sys.exit(0)
