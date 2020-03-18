#!/usr/bin/env python

import logging
import os
import shutil
import json

from .tool import Tool
from .consts import Paths, Groups

logger = logging.getLogger(__name__)

class ClusterProvisioning():
    
    def __init__(self, context):
        self.context = context

    def run(self):
        # check for the CA certificate, if 'k8s_certs_mode' == 'CA'
        k8s_certs_mode = self.context.config['k8s_certs_mode']
        logger.debug("k8s_certs_mode=%s" % k8s_certs_mode)

        if(k8s_certs_mode == 'CA'):
            # "CA" mode
            self.provision_ca()
        else:
            # "ACME" mode
            # create the cacrt.pem file for apiserver OIDC
            with open(Paths.sys_cacrt, "wb") as f:
                f.write(self.context.config["k8s_certs_acme"]["ca_certificate"])

        tool = Tool(self.context)

        logger.info("Prepare nodes, evaluate and fetch the current state")
        # tool.ansible_playbook_auto("./lib/ansible/clusterprovisioning/p0-prepare.yml")

        logger.info("Read state and build provisioning plan")
        state = self.read_state()
        logger.debug(state)
        plan = self.build_plan(state, self.context.config["k8s_version"])

        for step in plan:
            logger.info("- %s: %s" % (step.group, step.description))

    class ProvisionStep():
        """This is the base class for provisioning steps"""
        
        def __init__(self, group):
            self.group = group

        def gapply(self, groupstate):
            raise Exception("Not implemented")

        def vapply(self, state):
            self.gapply(state[self.group])

        def getprerequisites(self):
            return []

    class PSKubeBins(ProvisionStep):
        def __init__(self, group, tool, version):
            super().__init__(group)
            self.tool = tool
            self.version = version
            self.description = "version %s of %s installed" % (self.version, self.tool)

        def gapply(self, groupstate):
            for nodestate in groupstate:
                nodestate[self.tool] = self.version

    class PSClusterInit(ProvisionStep):
        def __init__(self, k8sversion):
            self.group = Groups.lnxclp_setup
            self.k8sversion = k8sversion
            self.description = "Initialize the cluster to k8s-version: %s" % k8sversion

        def gapply(self, groupstate):
            groupstate[0]["server"] = self.k8sversion

        def getprerequisites(self):
            return [ClusterProvisioning.PSKubeBins(Groups.lnxclp_setup, "kubeadm", self.k8sversion),
                ClusterProvisioning.PSKubeBins(Groups.lnxclp_setup, "kubelet", self.k8sversion),
                ClusterProvisioning.PSKubeBins(Groups.lnxclp_setup, "kubectl", self.k8sversion)]

    class PSJoinClp(ProvisionStep):
        def __init__(self):
            self.group = Groups.lnxclp
            self.description = "Join control plane nodes"

        def gapply(self, groupstate):
            pass

    class PSJoinLnxWrk(ProvisionStep):
        def __init__(self):
            self.group = Groups.lnxwrk
            self.description = "Join linux worker nodes"

    def build_plan(self, state, k8sversion):

        """
        Builds a provisioning plan based on the current state, and the requested k8s_version.
        It returns a list of 'ProvisionStep' instances
        """

        logger.info("Build a provisioning plan for k8s version '%s'" % k8sversion)

        res = []
        while True:
            stepres = self.build_plan_step(state, k8sversion)
            if not stepres or len(stepres) == 0: break

            for step in stepres:

                for pre in step.getprerequisites():
                    res.append(pre)

                res.append(step)

                step.vapply(state)
                # logger.debug(state)
                

        return res

    def build_plan_step(self, state, k8sversion):
        """
        Builds a provisioning plan based on the current state, and the requested k8s_version.
        It returns a list of 'ProvisionStep' instances
        """

        # check if cluster needs to be initialized by checking "server" of lnxclp_setup
        ####################################################
        if not state[Groups.lnxclp_setup][0]["server"]:
            return [ClusterProvisioning.PSClusterInit(k8sversion)]

        # check if new control plane nodes need to be joined
        ####################################################
        def noserver(n):
            not n["server"]

        unjoined = filter(noserver, state[Groups.lnxclp])
        if unjoined:
            return [ClusterProvisioning.PSJoinClp()]

    def read_state(self):
        """
        Reads the content of the ~/.k8s-setup/facts directory
        The directory is organized according to the "groups" ansible variable.
        The name of the Groups are the keys, the value is a list of the deserialized json files.
        A 'name' property is added to each value, containing the name of the file,
        which is also the name of the node. The json files are only deserialized once, and referenced
        by one or more groups. This is important to apply state changes.

        Example of returned dict:

        {
        "all": [
            {"name":"lnxclp1", "kubectl":"1.16.3", "kublet": "1.16.3", "kubeadm": "1.16.4", "server":""},
            {"name":"lnxwrk1", "kubectl":"1.16.3", "kublet": "1.16.3", "kubeadm": "1.16.4", "server":""}
        ],
        "lnxclp": [
            {"name":"lnxclp1", "kubectl":"1.16.3", "kublet": "1.16.3", "kubeadm": "1.16.4", "server":""}
        ],
        "lnxwrk": [
            {"name":"lnxwrk1", "kubectl":"1.16.3", "kublet": "1.16.3", "kubeadm": "1.16.4", "server":""}
        ]

        """

        res = {}
        nodes = {}

        def load(nodename):
            if res.get(nodename):
                return res.get(nodename)

            with open(os.path.join(Paths.sys_factsdir, nodename), "r") as file:
                state = json.load(file)
                state["name"] = nodename

            res[nodename] = state
            return state

        # open "GROUPS" index file
        with open(Paths.sys_factsgroups, "r") as file:
            groups = json.load(file)

        # load file contents
        for group in groups.keys():
            res[group] = nodes = []
            for nodename in groups[group]:
                nodes.append(load(nodename))

        return res

    def provision_ca(self):
        from .cert import generate_selfsigned_ca

        crtpath = None
        keypath = None

        if self.context.config['k8s_certs_ca']['generate']:
            crtpath = Paths.sys_cacrt
            keypath = Paths.sys_cakey
            logger.debug("Check if %s and %s exists" % (crtpath, keypath))

            if os.path.isfile(crtpath) and os.path.isfile(keypath):
                logger.info("CA already generated in %s %s" % (crtpath, keypath))
            else:
                logger.info("Generate CA files to %s %s" % (crtpath, keypath))
                crt, key = generate_selfsigned_ca("generated-ca.k8stest.local")

                with open(crtpath, "wb") as f:
                    f.write(crt)

                with open(keypath, "wb") as f:
                    f.write(key)

        else:
            crtpath=self.context.config["k8s_certs_ca"]["crt_filepath"]
            keypath=self.context.config["k8s_certs_ca"]["key_filepath"]

            if os.path.isfile(crtpath) and os.path.isfile(keypath):
                logger.info("Using configured ca-files: %s %s" % (crtpath, keypath))

                # TODO: validate that the files are ok

            # copy the crtfile, because this is needed for apiserver OIDC
            logger.debug("Copy ca file %s to %s" % (crtpath, Paths.sys_cacrt))
            shutil.copyfile(crtpath, Paths.sys_cacrt)

        # symlink the files to the chart, because helm can't access files
        # outside of the chart directory
        cafilespath = os.path.join(os.path.abspath(os.path.dirname(__file__)), "./lib/charts/wd-certmanager/.ca")
        cafilespath = os.path.relpath(cafilespath)
        logger.debug("Using path %s to symlink ca-files" % cafilespath)

        # always recreate links
        if os.path.isdir(cafilespath):
            shutil.rmtree(cafilespath)

        # the .ca file is in .gitignore, so it's ok to keep the links (for debugging)
        os.mkdir(cafilespath)
        os.symlink(os.path.abspath(crtpath), os.path.join(cafilespath, "cacrt.pem"))
        os.symlink(os.path.abspath(keypath), os.path.join(cafilespath, "cakey.pem"))

