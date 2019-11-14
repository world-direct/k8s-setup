#!/usr/bin/env python

import logging
logger = logging.getLogger("main")

from args import parse_args
from tool import Tool
from context import Context
from provision import Provision

def cmd_info(args):
    logger.debug('cmd:info()')

    print('not implemented')
    exit(1)

def cmd_checkout(args):
    logger.debug('cmd:checkout(version=%s, no_deps=%i)' % (args.version, args.no_deps))
    
    print('not implemented')
    exit(1)

def cmd_config(args):
    logger.debug ('cmd:config(file=%s)' % args.file)
    context.setfile(args.file)

def cmd_provision(args):
    logger.debug ('cmd:provision(scope=%s, ansible_options=%s)' % (args.scope, args.ansible_options))

    p = Provision(context)
    fn = getattr(p, args.scope)
    fn()

def cmd_tool(args):
    logger.debug ('cmd:tool(name=%s, show_only=%d, toolargs=%s)' % (args.name, args.show_only, args.toolargs))
    tool = Tool(context)
    rc = tool.run(args.name, args.toolargs)
    exit(rc)

res=parse_args()

if res.debug:
    logging.basicConfig(level=logging.DEBUG)

# get execution context
context = Context()

commandfn=globals()["cmd_" + res.command]
commandfn(res)
