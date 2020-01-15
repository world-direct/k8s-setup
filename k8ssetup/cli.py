#!/usr/bin/env python

import click

@click.group()
def cli():
    pass

@click.command()
def info():
    """Shows the current version and configuration info"""
    click.echo('cmd_info')

cli.add_command(info)

@click.group()
def config():
    """Performs configuration commands"""
    
    @click.command()
    @click.option("--file", help="Specifies the global configuration file")
    def set(file):
        click.echo("config set file %s " % file)

    config.add_command(set)

cli.add_command(config)

@click.command()
def provision():
    """Performs the provisioning"""
    click.echo('cmd_provision')

cli.add_command(provision)

@click.command()
def tool():
    """Allows executing the underlying tools for diagnostics"""
    click.echo('cmd_tool')

cli.add_command(tool)

@click.command()
def generate():
    """Generators (for /etc/hosts)"""
    click.echo('cmd_generate')

cli.add_command(generate)

def main():
    cli()
