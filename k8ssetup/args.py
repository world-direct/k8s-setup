#!/usr/bin/env python

import argparse
import sys
import os

def parse_args():

    class Args(object):
        
        def __init__(self, command):
            self.command = command
            self.debug = True if os.environ.get("K8S_SETUP_DEBUG") else False

            # additional attributes are added in each subparser
        pass

    # https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
    class ArgsParser(object):

        def __init__(self):
            parser = argparse.ArgumentParser(
                prog='k8s-setup',
                description='cli tool for k8s-setup',
                usage='''k8s-setup <command> [<args>]

    The subcommands commands are:
        info        Shows the current version and configuration info
        config      Performs configuration commands
        provision   Performs the provisioning
        tool        Allows executing the underlying tools for diagnostics
        generate    Generators (for /etc/hosts)
    ''')

            parser.add_argument('command', help='Subcommand to run')
            # parse_args defaults to [1:] for args, but you need to
            # exclude the rest of the args too, or validation will fail
            args = parser.parse_args(sys.argv[1:2])
            if not hasattr(self, args.command):
                print('Unrecognized command')
                parser.print_help()
                exit(1)
            # use dispatch pattern to invoke method with same name
            self.result = getattr(self, args.command)()

        def info(self):
            parser = argparse.ArgumentParser(prog='k8s-setup info',
                description='Shows the current version and configuration info')

            parser.parse_args(sys.argv[2:])
            res = Args("info")
            return res

        def checkout(self):
            parser = argparse.ArgumentParser(prog='k8s-setup checkout',
                description='Download objects and refs from another repository')

            parser.add_argument('--no-deps',
                help="Don't automatically install dependencies",
                action='store_true'
            )

            parser.add_argument('version',
                help="The name of the git tag for the release, or 'latest'",
                default='latest',
                nargs="?"
            )

            args = parser.parse_args(sys.argv[2:])

            res = Args('checkout')
            res.version = args.version
            res.no_deps = args.no_deps
            return res

        def config(self):
            parser = argparse.ArgumentParser(prog='k8s-setup config',
                description='Performs configuration commands')

            parser.add_argument(
                "operation", help="must be 'set'",
                choices=["set"],
                nargs=1)

            parser.add_argument('--file',
                help="Specifies the global configuration file",
                nargs='?',
                default=''
            )

            parser.add_argument('--value',
                help="Specifies a single configuration value (key=value)",
                nargs='?',
                default=''
            )

            args = parser.parse_args(sys.argv[2:])

            if not args.value and not args.file:
                print("Eighter --file or --value has to be specified")
                exit(1)

            res = Args('config')
            res.file = args.file
            res.value = args.value
            
            return res

        def provision(self):
            parser = argparse.ArgumentParser(prog='k8s-setup provision',
                description='Performs provisioning')

            parser.add_argument('scope', 
                help="Sets the configuration file in the user profile",
                choices=['all', 'hosts', 'cluster', 'incluster'],
                default='all',
                nargs='?')

            parser.add_argument('--ansible-options',
                help="Pass additional arguments to ansible-playbook",
                nargs='?',
                default=''
            )
            args = parser.parse_args(sys.argv[2:])

            res = Args('provision')
            res.scope = args.scope
            res.ansible_options = args.ansible_options
            return res

        def tool(self):
            parser = argparse.ArgumentParser(prog='k8s-setup tool',
                description='Allows to execute the underlying tool cli programs')

            parser.add_argument('name', 
                help="The tool name",
                choices=['ansible', 'ansible-playbook', 'ansible-inventory', 'vagrant'],
                nargs=1,
                action='store')

            parser.add_argument('-s', '--show-only',
                help="Don't execute the tool, only show the commandline",
                action='store_true'
            )

            parser.add_argument('toolargs',
                help="Pass args directly to the tool",
                nargs=argparse.REMAINDER,
                default=''
            )
            args = parser.parse_args(sys.argv[2:])

            res = Args('tool')
            res.name = args.name[0]
            res.show_only = args.show_only
            res.toolargs = args.toolargs
            return res

        def generate(self):
            parser = argparse.ArgumentParser(prog='k8s-setup generate',
                description='Generates artifactes')

            parser.add_argument('type', 
                help="the type of the artifact",
                choices=['hostsfile'],
                nargs='?')
            parser.add_argument('--merge',
                help="Merges the existing /etc/hosts",
                action='store_true'
            )

            args = parser.parse_args(sys.argv[2:])

            res = Args('generate')
            res.type = args.type
            res.merge = args.merge
            return res

    parser = ArgsParser()
    return parser.result