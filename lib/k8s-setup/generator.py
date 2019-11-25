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

        # rule tuple: (ip, host, comment)
        rules = []

        # API Server host
        cluster_dnsname = self.context.config["k8s_cluster_dnsname"]
        apiserverip = self.context.config["k8s_apiserver_vip"]
        apiserverhost = "%s.%s" % (self.context.config["k8s_apiserver_hostname"], cluster_dnsname)
        rules.append((apiserverip, apiserverhost, "apiserver (mandatory)"))

        # ingresses hosts
        ingressip=self.context.config["k8s_loadbalancers_ingress_ip"]
        for item in client.NetworkingV1beta1Api().list_ingress_for_all_namespaces().items:
            for rule in item.spec.rules:
                rules.append((ingressip, rule.host, "ingress rule" ))

        if merge:
            lines = tuple(open("/etc/hosts", "r"))

            # Merge algorithm:
            #   1. print each existing line, when it is not
            #       - parsable (blank, comments, ...)
            #       - containing a hostname which ends with 
            #   2. print 'header'
            #   3. print our rules

            for line in lines:

                # parse line into tuple parts := (ip, host)
                parsed=()
                line = line.strip()
                parts = line.split()
                if(len(parts) < 2):
                    # unparsable
                    print(line)
                    continue;

                if not parts[1].endswith(cluster_dnsname):
                    # not one of our rules
                    print(line)

        # output our rules    
        for rule in rules:
            print("%-12s %-40s # k8s-setup: %s" % rule)
        