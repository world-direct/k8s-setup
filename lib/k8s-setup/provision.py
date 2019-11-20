#!/usr/bin/env python

import logging

from tool import Tool

logger = logging.getLogger(__name__)

class Provision():
    
    def __init__(self, context):
        self.context = context

    def hosts(self):
        logger.info("Provisioning scope 'hosts'")

        tool = Tool(self.context)
        if(self.context.mode == "vagrant"):
            # run 'vagrant up', which runs also the vagrant playbook
            tool.run("vagrant", ["up", "--provision"])
        else:
            tool.ansible_playbook_auto("./lib/ansible/ping.yml")

        # run the 'hosts.yml'
        tool.ansible_playbook_auto("./lib/ansible/hosts.yml", become = True)

    def cluster(self):
        logger.info("Provisioning scope 'cluster'")

        tool = Tool(self.context)
        tool.ansible_playbook_auto("./lib/ansible/cluster.yml", become = True)
        tool.ansible_playbook_auto("./lib/ansible/cluster-local.yml", add_localhost=True, become=False)

    def incluster(self):
        logger.info("Provisioning scope 'incluster'")

        tool = Tool(self.context)
        tool.ansible_playbook_auto("./lib/ansible/incluster.yml", add_localhost=True, become=False)

    def all(self):
        self.hosts()
        self.cluster()
        self.incluster()
