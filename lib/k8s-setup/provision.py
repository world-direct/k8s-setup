#!/usr/bin/env python

import logging

from tool import Tool

class Provision():
    
    def __init__(self, context):
        self.context = context

        if(self.context.mode == "vagrant"):
            # This is the path where the Vagrant Provisioner writes the inventory file
            # The Tool checks if this file exists, before running vagrant
            # So this also works when no file has been generated yet.
            # It will be generated in the 'hosts' scope by executing the 
            # 'vagrant.yml' playbook
            self.context.ansible_inventory_file = "./lib/vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory"

    def hosts(self):
        logging.info("Provisioning scope 'hosts'")

        tool = Tool(self.context)
        if(self.context.mode == "vagrant"):
            # run 'vagrant up', which runs also the vagrant playbook
            tool.run("vagrant", ["up", "--provision"])
        else:
            tool.ansible_playbook_auto("./lib/ansible/ping.yml")

        # run the 'hosts.yml'
        tool.ansible_playbook_auto("./lib/ansible/hosts.yml", become = True)

    def cluster(self):
        logging.info("Provisioning scope 'cluster'")

        tool = Tool(self.context)
        tool.ansible_playbook_auto("./lib/ansible/cluster.yml", become = True)

    def incluster(self):
        logging.info("Provisioning scope 'incluster'")

        tool = Tool(self.context)
        tool.ansible_playbook_auto("./lib/ansible/incluster.yml", add_localhost=True, become=False)

    def all(self):
        self.hosts()
        self.cluster()
        self.incluster()
