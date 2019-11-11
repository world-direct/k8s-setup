#!/usr/bin/env python

import logging

from args import parse_args

def info(args):
    logging.debug('cmd:info()')

def checkout(args):
    logging.debug('cmd:checkout(version=%s, no_deps=%i)' % (args.version, args.no_deps))

def config(args):
    logging.debug ('cmd:config(file=%s)' % args.file)

def provision(args):
    logging.debug ('cmd:provision(scope=%s, ansible_options=%s)' % (args.scope, args.ansible_options))

def tool(args):
    logging.debug ('cmd:tool(name=%s, show_only=%d, toolargs=%s)' % (args.name, args.show_only, args.toolargs))

res=parse_args()

if res.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

commandfn=globals()[res.command]
commandfn(res)
