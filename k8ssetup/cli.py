#!/usr/bin/env python

# https://click.palletsprojects.com/en/7.x/complex/


import click
import sys

import logging
logger = logging.getLogger(__name__)

from .context import Context

pass_context = click.make_pass_decorator(Context)

@click.group()
@click.option("--debug", "-d", is_flag=True, help="Outputs debug level log messages")
@click.version_option()
@click.pass_context
def cli(clickctx, debug):

    
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s" \
            if debug else \
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

    clickctx.obj = Context()
    pass

#######################################
## k8s-setup info
@cli.command()
@pass_context
def info(context):
    """Shows the current version and configuration info"""

    from .info import Info
    info = Info(context)
    info.run(sys.stdout)
    exit(0)

#######################################
## k8s-setup config
@cli.group()
@pass_context
def config(context):
    """Performs configuration commands"""
    pass

@config.command("set")
@click.option("--file", type=click.Path(exists=True, readable=True))
@click.option("--value", type=click.STRING)
@pass_context
def config_set(context, file, value):
    logger.debug ('cmd:config(file=%s, value=%s)' % (file, value))

    if(file):
        context.set_file(file)
    elif(value):
        parts = value.split('=')
        if len(parts) != 2:
            print("The value must be specified with key=value")
            exit(1)

        context.set_config_value(parts[0], parts[1])

#######################################
## k8s-setup vagrant
@cli.group()
@pass_context
def vagrant(context):
    """Executes vagrant commands"""
    pass

@vagrant.command("ssh")
@click.argument("machine", type=click.STRING, required=True)
@pass_context
def vagrant_ssh(context, machine):
    logger.debug ('cmd:vagrant-ssh(machine=%s)' % (machine))
    from .tool import Tool
    tool = Tool(context)
    return tool.run("vagrant", ["ssh", machine])

@vagrant.command("destroy")
@click.argument("machine", type=click.STRING, required=False)
@pass_context
def vagrant_destroy(context, machine):
    logger.debug ('cmd:vagrant-ssh(machine=%s)' % (machine))
    from .tool import Tool
    tool = Tool(context)
    args = ["destroy"]

    if machine:
        args.append(machine)

    args.append("-f")

    return tool.run("vagrant", args)

#######################################
## k8s-setup provision

@cli.command()
@click.argument(
    'scope', 
    type=click.Choice(['all', 'hosts', 'cluster', 'incluster']), 
    nargs=-1)
@click.option("--ansible-options", type=click.STRING, help="additional options for ansible")
@pass_context
def provision(context, scope, ansible_options):
    """Performs the provisioning"""

    if not scope: scope=["all"]

    logger.debug ('cmd:provision(scope=%s, ansible_options=%s)' % (scope, ansible_options))

    from .provision import Provision
    provision = Provision(context)
    
    if "all" in scope: provision.all()
    if "hosts" in scope: provision.hosts()
    if "cluster" in scope: provision.cluster()
    if "incluster" in scope: provision.incluster()

#######################################
## k8s-setup tool

@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
#@click.option('--show-only', type=click.BOOL, help="Don't execute the tool, only show the commandline")
@click.argument('name', type=click.STRING)
@click.argument('toolargs', nargs=-1, type=click.UNPROCESSED)
@pass_context
def tool(context, name, toolargs):
    """Allows executing the underlying tools for diagnostics"""
    
    from .tool import Tool

    if isinstance(toolargs, tuple): toolargs=list(toolargs)    
    if isinstance(toolargs, list): toolargs=" ".join(toolargs)
    logger.debug ('cmd:tool(name=%s, toolargs=\'%s\')' % (name, toolargs))

    toolargs = [toolargs]

    tool = Tool(context)
    rc = tool.run(name, toolargs)
    exit(rc)

#######################################
## k8s-setup generate

@cli.command()
@click.argument("type", type=click.Choice(["hostsfile"]))
@click.option("--merge", type=click.BOOL, help="Merges the existing /etc/hosts", default=False)
@pass_context
def generate(context, type, merge):
    """Generators (for /etc/hosts)"""

    from .generator import Generator

    logger.debug ('cmd:generate(type=%s, merge=%d)' % (type, merge))
    generator = Generator(context)

    if type == "hostsfile":
        rc = generator.hostsfile(merge)
        exit(rc)

    exit(1)
    

def main():
    # pylint: disable=unexpected-keyword-arg
    # pylint: disable=no-value-for-parameter
    cli(auto_envvar_prefix="K8S_SETUP")