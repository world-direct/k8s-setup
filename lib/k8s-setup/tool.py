#!/usr/bin/env python

import subprocess
import logging
import os

from context import Context

class Tool(object):
    
    def __init__(self, context):
        self.context = context

    def add_default_args(program, args):
        pass

    def get_cwd(self, program):

        if program == "vagrant":
            return "./lib/vagrant"

        return "."

    def run(self, program, args):
        program = str(program)
        env = self.context.get_environment()

        args = [program] + args

        logging.debug("$ " + " ".join(args))

        sb = subprocess.call(
            args, 
            cwd=self.get_cwd(program), 
            env=env)

    def ansible_playbook_auto(self, playbook_path, add_localhost = False, become = False):

        args = []
        if(os.path.exists(self.context.inventory_file_path)):
            args.append("--inventory-file=%s" % self.context.inventory_file_path)
        
        if(self.context.mode == "vagrant"):
            args.append("--ssh-extra-args='-o StrictHostKeyChecking=no'")

        for config_file in self.context.config_files:
            args.append("-e@%s" % config_file)

        if become:
            args.append("--become")

        limit = ["all"]

        if add_localhost:
            limit.append("localhost")

        limit = ",".join(limit)
        if(limit):
            args.append("--limit=%s" % limit)

        args.append(playbook_path)

        return self.run("ansible-playbook", args)
