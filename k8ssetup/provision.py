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

        logger.debug("Write k8s-setup-info")
        from .info import Info
        with open(Paths.sys_homeroot + "/k8s-setup-info", 'w') as fs:
            Info(self.context).run(fs)

        # check for the CA certificate, if 'k8s_certs_mode' == 'CA'
        k8s_certs_mode = self.context.config['k8s_certs_mode']
        logger.debug("k8s_certs_mode=%s" % k8s_certs_mode)

        if(k8s_certs_mode == 'CA'):
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

        # "ACME" mode
        else:
            # create the cacrt.pem file for apiserver OIDC
            with open(Paths.sys_cacrt, "wb") as f:
                f.write(self.context.config["k8s_certs_acme"]["ca_certificate"])

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
