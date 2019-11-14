#!/usr/bin/env python

import subprocess
import logging
import os

from context import Context

logger = logging.getLogger(__name__)

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

        cwd = os.path.abspath(self.get_cwd(program))
        logger.debug("RUN in '%s': %s" % (cwd, " ".join(args)))

        rc = subprocess.call(
            args, 
            cwd=cwd, 
            env=env)

        logger.debug("EXIT rc=%d" % rc)
        return rc

    def ansible_playbook_auto(self, playbook_path, add_localhost = False, become = False, dont_check_exitcode = False):

        args = []
        if(os.path.exists(self.context.ansible_inventory_file)):
            args.append("--inventory-file=%s" % self.context.ansible_inventory_file)
        
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

        rc = self.run("ansible-playbook", args)

        if not dont_check_exitcode and rc != 0:
            exit(rc)

        return rc