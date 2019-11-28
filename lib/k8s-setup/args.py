#!/usr/bin/env python

import argparse
import sys

def parse_args():

    class Args(object):
        
        def __init__(self, command, debug):
            self.command = command
            self.debug = debug
            # additional attributes are added in each subparser
        pass

    # https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
    class ArgsParser(object):

        def add_global_args(self, parser):
            """
            This function adds global args to all subparsers.
            I tried to add them in the toplevep 'parser', but I didn't manage
            to get it work in 3 minutes.
            Because I'm late in the schedule, I may try later to improve this.
            TODO: Check top level args
            """

            parser.add_argument('-d', '--debug',
                help="Enable debug log to stdout",
                action='store_true',
                default=False
            )

        def __init__(self):
            parser = argparse.ArgumentParser(
                prog='k8s-setup',
                description='cli tool for k8s-setup',
                usage='''k8s-setup <command> [<args>]

    The subcommands commands are:
        info        Shows the current version and configuration info
        checkout    Checks out a specific release, and installs the prequisites
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

            self.add_global_args(parser)

            args = parser.parse_args(sys.argv[2:])
            res = Args("info", args.debug)
            return res

        def checkout(self):
            parser = argparse.ArgumentParser(prog='k8s-setup checkout',
                description='Download objects and refs from another repository')

            self.add_global_args(parser)

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

            res = Args('checkout', args.debug)
            res.version = args.version
            res.no_deps = args.no_deps
            return res

        def config(self):
            parser = argparse.ArgumentParser(prog='k8s-setup config',
                description='Performs configuration commands')

            self.add_global_args(parser)

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

            res = Args('config', args.debug)
            res.file = args.file
            res.value = args.value
            
            return res

        def provision(self):
            parser = argparse.ArgumentParser(prog='k8s-setup provision',
                description='Performs provisioning')

            self.add_global_args(parser)

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

            res = Args('provision', args.debug)
            res.scope = args.scope
            res.ansible_options = args.ansible_options
            return res

        def tool(self):
            parser = argparse.ArgumentParser(prog='k8s-setup tool',
                description='Allows to execute the underlying tool cli programs')

            self.add_global_args(parser)
            
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

            res = Args('tool', args.debug)
            res.name = args.name[0]
            res.show_only = args.show_only
            res.toolargs = args.toolargs
            return res

        def generate(self):
            parser = argparse.ArgumentParser(prog='k8s-setup generate',
                description='Generates artifactes')

            self.add_global_args(parser)

            parser.add_argument('type', 
                help="the type of the artifact",
                choices=['hostsfile'],
                nargs='?')
            parser.add_argument('--merge',
                help="Merges the existing /etc/hosts",
                action='store_true'
            )

            args = parser.parse_args(sys.argv[2:])

            res = Args('generate', args.debug)
            res.type = args.type
            res.merge = args.merge
            return res

    parser = ArgsParser()
    return parser.result