#!/usr/bin/env python

# https://click.palletsprojects.com/en/7.x/complex/


import click
import logging
from context import Context
import sys

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
    click.echo('cmd_info')

    from info import Info
    info = Info(context)
    info.run(sys.stdout)
    exit(0)

#######################################
## k8s-setup config

@cli.command()
@pass_context
def config(context):
    """Performs configuration commands"""

#######################################
## k8s-setup provision

@cli.command()
def provision():
    """Performs the provisioning"""
    click.echo('cmd_provision')

#######################################
## k8s-setup tool

@cli.command()
def tool():
    """Allows executing the underlying tools for diagnostics"""
    click.echo('cmd_tool')

#######################################
## k8s-setup generate

@cli.command()
def generate(artifact):
    """Generators (for /etc/hosts)"""

def main():
    cli(auto_envvar_prefix="K8S_SETUP")