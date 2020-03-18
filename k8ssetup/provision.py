#!/usr/bin/env python

import logging
import os
import shutil

from .tool import Tool
from .consts import Paths

logger = logging.getLogger(__name__)

class Provision():
    
    def __init__(self, context):
        self.context = context

    def started(self):
        if(self.context.mode == "vagrant"):

            logger.info("Ensure vagrant hosts started")
            tool = Tool(self.context)

            # run 'vagrant up', which runs also the vagrant playbook
            tool.run("vagrant", ["up", "--provision"])

    def hosts(self):
        logger.info("Provisioning scope 'hosts'")
        self.started()

        tool = Tool(self.context)
        
        # run the 'hosts.yml'
        tool.ansible_playbook_auto("./lib/ansible/hosts.yml", become = True)

    def cluster(self):
        logger.info("Provisioning scope 'cluster'")
        # self.started()

        from .clusterprovisioning import ClusterProvisioning
        clusterprovisioning = ClusterProvisioning(self.context)
        clusterprovisioning.run()

        exit(0)

        tool.ansible_playbook_auto("./lib/ansible/cluster.yml", become = True)
        tool.ansible_playbook_auto("./lib/ansible/cluster-local.yml", add_localhost=True, become=False)

    def incluster(self):
        logger.info("Provisioning scope 'incluster'")
        self.started()

        tool = Tool(self.context)
        tool.ansible_playbook_auto("./lib/ansible/incluster.yml", add_localhost=True, become=False)

    def all(self):
        self.hosts()
        self.cluster()
        self.incluster()
