#!/usr/bin/env python

import logging
logger = logging.getLogger("main")

from args import parse_args
from tool import Tool
from context import Context
from provision import Provision
from generator import Generator

def main():

    args=parse_args()
    setup_logging(args)

    # get execution context
    context = Context()

    commandfn=globals()["cmd_" + args.command]
    commandfn(context, args)

def cmd_info(context, args):
    logger.debug('cmd:info()')

    import subprocess
    import os
    import yaml

    # It would be way better to preserve insertion order
    # For python, you have to use a 'collections.OrderedDict' object
    # But pyyaml 5.2 (installed with pip) don't handle OrderDict.
    # This should work and is documented, and also implemented in source:
    # https://github.com/yaml/pyyaml/blob/5.2/lib3/yaml/representer.py#L358
    # But when debugging, the file is different. This seems more a pip issue. 
    # TODO: Fix ordering
    vals = dict()

    # version
    versionsh = os.path.abspath(os.path.join(os.path.dirname(__file__), "../version.sh"))
    logger.debug("using script %s" % versionsh)
    version=subprocess.check_output(versionsh).strip()
    vals["version"] = version

    # config metadata
    vals["config-files"] = context.config_files

    # important configuration values
    conf = dict()
    vals["configuration"] = conf
    conf["mode"] = context.mode
    conf["cluster-dns-name"] = context.config["k8s_cluster_dnsname"]
    conf["ansible_inventory_filepath"] = context.ansible_inventory_filepath
    conf["k8s-version"] = context.config["k8s_version"]

    if context.mode == "vagrant":
        conf["lnxclp-nodes"] = context.config["global_vagrant_lnxclp_count"]
        conf["lnxwrk-nodes"] = context.config["global_vagrant_lnxwrk_count"]
        conf["winwrk-nodes"] = context.config["global_vagrant_winwrk_count"]

    out = yaml.dump(vals, Dumper=yaml.SafeDumper)
    print(out)

    exit(0)

def cmd_checkout(context, args):
    logger.debug('cmd:checkout(version=%s, no_deps=%i)' % (args.version, args.no_deps))
    
    print('not implemented')
    exit(1)

def cmd_config(context, args):
    logger.debug ('cmd:config(file=%s, value=%s)' % (args.file, args.value))

    if(args.file):
        context.set_file(args.file)
    elif(args.value):
        parts = args.value.split('=')
        if len(parts) != 2:
            print("The value must be specified with key=value")
            exit(1)

        context.set_config_value(parts[0], parts[1])

def cmd_provision(context, args):
    logger.debug ('cmd:provision(scope=%s, ansible_options=%s)' % (args.scope, args.ansible_options))

    p = Provision(context)
    fn = getattr(p, args.scope)
    fn()

def cmd_tool(context, args):
    logger.debug ('cmd:tool(name=%s, show_only=%d, toolargs=%s)' % (args.name, args.show_only, args.toolargs))
    tool = Tool(context)
    rc = tool.run(args.name, args.toolargs)
    exit(rc)

def cmd_generate(context, args):
    logger.debug ('cmd:generate(type=%s, merge=%d)' % (args.type, args.merge))
    generator = Generator(context)

    if args.type == "hostsfile":
        rc = generator.hostsfile(args.merge)

    exit(rc)

def setup_logging(args):
    """Set up the logging."""
    """https://www.programcreek.com/python/example/357/logging.WARNING"""

    level = logging.DEBUG if args.debug else logging.INFO
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s" \
            if args.debug else \
        "%(asctime)s %(levelname)s %(message)s"

    logging.basicConfig(level=level)

    colorfmt = "%(log_color)s{}%(reset)s".format(fmt)
    datefmt = '%Y-%m-%d %H:%M:%S'

    # Suppress overly verbose logs from libraries that aren't helpful
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

    try:
        from colorlog import ColoredFormatter
        logging.getLogger().handlers[0].setFormatter(ColoredFormatter(
            colorfmt,
            datefmt=datefmt,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        ))
    except ImportError:
        pass

    logger = logging.getLogger('')
    logger.setLevel(level) 

main()