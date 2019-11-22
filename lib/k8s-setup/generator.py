#!/usr/bin/env python

import logging
import os

from context import Context

from kubernetes import config, client

logger = logging.getLogger(__name__)

class Generator(object):
    
    def __init__(self, context):
        self.context = context

    def hostsfile(self, merge):
        config.load_kube_config()

        # ip
        ip=self.context.config["k8s_loadbalancers_ingress_ip"]

        print("######################################################")
        print("# Hosts for Ingress Hosts, by k8s-setup ")
        print("#")

        if merge:
            print("merge not implemented yet")
            exit(1)
        else:
            print("# execute this command (with sudo) to register all ingress hosts:")
            print("# ./k8s-setup generate hostsfile --merge > /etc/hosts")

        print("######################################################")

        # get ingresses
        apiresp = client.NetworkingV1beta1Api().list_ingress_for_all_namespaces()

        for item in apiresp.items:
            for rule in item.spec.rules:
                print("%s   %s" % (ip, rule.host))