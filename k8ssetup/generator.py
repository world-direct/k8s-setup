#!/usr/bin/env python

import logging
import os

from .context import Context

logger = logging.getLogger(__name__)

class Generator(object):
    
    def __init__(self, context):
        self.context = context

    def hostsfile(self, merge):
        from kubernetes import config, client
        import requests

        # SSL Verification:
        # Because we use self-signed certs (at least for Vagrant-Mode), we
        #   - use verify=False on GET
        #   - disable the 'InsecureRequestWarning', which would get printed to stderr:
        #
        # urllib3/connectionpool.py:1004: InsecureRequestWarning: 
        # Unverified HTTPS request is being made. Adding certificate verification is strongly advised. #
        # See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # load the default config
        config.load_kube_config()

        # rule tuple: (ip, host, comment)
        rules = []

        # API Server host
        cluster_dnsname = self.context.config["k8s_cluster_dnsname"]
        apiserverip = self.context.config["k8s_apiserver_vip"]
        apiserverhost = "%s.%s" % (self.context.config["k8s_apiserver_hostname"], cluster_dnsname)
        rules.append((apiserverip, apiserverhost, "apiserver (mandatory)"))

        # test if cluster is running
        running=False
        try:
            healthz = "https://%s/healthz" % apiserverip
            logger.debug("GET %s" % healthz)
            res = requests.get(healthz, verify=False)
            logger.debug("%d %s" % (res.status_code, res.reason))
            running = res.status_code == 200
        except requests.exceptions.ConnectionError as err:
            logger.exception(err)
            if(err.response):
                logger.debug("%d %s" % (err.response.status_code, err.response.reason))

        # ingresses hosts
        if running:
            ingressip=self.context.config["k8s_loadbalancers_ingress_ip"]
            for item in client.NetworkingV1beta1Api().list_ingress_for_all_namespaces().items:
                for rule in item.spec.rules:
                    rules.append((ingressip, rule.host, "ingress rule" ))
        else:
            logger.warning("Unable to connect to kuberneetes endpoint. Only the apiserver host is created")

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
                line = line.strip()
                parts = line.split()
                if(len(parts) < 2):
                    # unparsable
                    print(line)
                    continue

                if not parts[1].endswith(cluster_dnsname):
                    # not one of our rules
                    print(line)

        # output our rules
        for rule in rules:
            print("%-12s %-40s # k8s-setup: %s" % rule)
        