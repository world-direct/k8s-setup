#!/usr/bin/env python

import os
import sys
import yaml
import shutil

import logging
logger = logging.getLogger(__name__)

from .consts import Paths

class Context(object):

    def __init__(self):

        srcdir = os.path.dirname(__file__)
        curdir = os.path.abspath(os.curdir)

        if srcdir != curdir:
            logger.debug("Setting current directory from %s to %s" % (curdir, srcdir))
            os.chdir(srcdir)

        # ensure directories
        def checkdir(dir):
            if not os.path.isdir(dir):
                logger.debug("Creating required directoy %s" % dir)
                os.mkdir(dir)

        checkdir(Paths.sys_homeroot)

        def add_config_file(file):

            file = os.path.normpath(file)

            if os.path.islink(file):
                linkedto=os.path.normpath(os.readlink(file))
                logger.debug("Using %s -> %s configuration file" % (file, linkedto))
                file = linkedto
            else:
                logger.debug("Using %s configuration file" % file)

            self.config_files.append(file)

        def read_config_file(filepath):

            with open(filepath, 'r') as fs:
                doc = yaml.load(fs.read(), Loader=yaml.SafeLoader)
                if len(doc) == 0:
                    return None
                
                # all values ending with 'filepath' rewritten to an absolute path, 
                # based on pathname(path)
                for name in doc.keys():
                    if not name.endswith("filepath"): continue

                    val = doc[name]

                    if not val:
                        # empty value
                        continue

                    if not os.path.isabs(val):

                        dirname = os.path.dirname(
                            filepath if filepath != Paths.sys_currentconfig else os.readlink(filepath)
                        )

                        absval = os.path.relpath(os.path.join(dirname, val))
                        logger.debug("'%s' configuration rewritten to absolute path %s" % (name, absval))
                        doc[name] = absval

                # reserialize to yaml and return
                return yaml.dump(doc, Dumper=yaml.SafeDumper)

        ## Read configuration
        #############################################################
        self.config_files = []  # from lowest to highest priority
        add_config_file(Paths.src_confdefaults)

        # read the current config
        if os.path.islink(Paths.sys_currentconfig):
            add_config_file(Paths.sys_currentconfig)
        else:
            logger.debug("'%s' doesnt exist, defaulting to %s" % (Paths.sys_currentconfig, Paths.src_confvagrant))
            add_config_file(Paths.src_confvagrant)

        # add private config if set
        if os.path.isfile(Paths.sys_cliconfig):
            add_config_file(Paths.sys_cliconfig)

        # TODO: check if all self.config_files exists

        # To apply defaults, we make a very simple merge, that combines the content
        # of the file in the right order, and then feed it to yaml.load
        # Yaml ignores redefined mappings, so merged file need to be sorted from
        # highest to lowest priority. 'defaults.yml' is the last one
        self.config_string = ""
        for config_file in self.config_files:
            val = read_config_file(config_file)
            if val:
                self.config_string = self.config_string + "\n" + val

        self.config = yaml.load(self.config_string, Loader=yaml.SafeLoader)

        # TODO: check if global_mode exists, and if it is 'vagrant' or 'production'
        self.mode = self.config['global_mode']
        self.ansible_inventory_filepath = self.config['ansible_inventory_filepath']
        
        try:
            self.validate_config()
        except ValueError as err:
            logger.error(str(err))
            exit(1)

        if self.mode == "vagrant":
            # vagrant places the .vagrant directory relative to the Vagrantfile
            # because we should not put anything in the python dist-packages,
            # we will copy the vagrantfile to /var/k8s-setup/Vagrantfile
            if not os.path.islink(Paths.sys_vagrantfile):
                os.symlink(os.path.abspath(Paths.src_vagrantfile), Paths.sys_vagrantfile)

            # to generate the inventory, we need to provide a playbook file (lib/ansible/vagrantpp.yml)
            # because we are running from ~/.k8s-setup, this can't be bound to the source path
            # so we link it here to ~/.k8s-setup/vagrantpp.yml
            if not os.path.islink(Paths.sys_vagrantpp):
                os.symlink(os.path.abspath(Paths.src_vagrantpp), Paths.sys_vagrantpp)

            self.ansible_inventory_filepath = Paths.sys_vagrantgeneratedinventory

        logger.debug("Using mode '%s', inventory-file '%s'" % (self.mode, self.ansible_inventory_filepath))

    def validate_config(self):
        logger.debug("validating config")

        c = self.config

        k8s_certs_mode = c["k8s_certs_mode"]
        logger.debug("k8s_certs_mode: %s" % k8s_certs_mode)

        if k8s_certs_mode != "CA" and k8s_certs_mode != "ACME":
            raise ValueError('k8s_certs_mode need to be "CA" or "ACME"')

        if k8s_certs_mode == "ACME" and not c["k8s_certs_acme"]["ca_certificate"]:
            raise ValueError('k8s_certs_mode "ACME" needs the pem encoded ca certificate in k8s_certs_acme.ca_certificate')

        if c["k8s_apiserver_vip_virtual_router_id"] == -1:
            raise ValueError('k8s_apiserver_vip_virtual_router_id is mandatory, but not set')

    def set_file(self, filepath):

        if not os.path.isfile(filepath):
            print("File '%s' not found. Exiting" % filepath)
            exit(1)

        if os.path.islink(Paths.sys_currentconfig):
            logger.debug("'%s' exist. Removing" % (Paths.sys_currentconfig))
            os.remove(Paths.sys_currentconfig)

        logger.debug("Creating symlink '%s' --> '%s'" % (Paths.sys_currentconfig, filepath))
        os.symlink(filepath, Paths.sys_currentconfig)

    def set_config_value(self, name, value):
        vals=None

        if os.path.isfile(Paths.sys_cliconfig):
            with open(Paths.sys_cliconfig, 'r') as fs:
                content = fs.read()
                vals = yaml.load(content, Loader=yaml.SafeLoader)

        vals = {} if not vals else vals

        if value:
            logger.debug("Setting private config %s=%s" % (name, value))
            vals[name]=value
        elif vals.has_key(name):
            logger.debug("Deleting private config %s=%s" % (name, value))
            del vals[name]

        with open(Paths.sys_cliconfig, 'w+') as fs:
            content = yaml.dump(vals, Dumper=yaml.SafeDumper)
            fs.write(content)

    def get_environment(self):

        env = os.environ.copy()

        # copy each global_vagrant_* setting
        for key in self.config.keys():
            if key.startswith('global_vagrant_'):
                env[key.upper()] = str(self.config[key])

        # provide the VAGRANT_APISERVER_IP and VAGRANT_APISERVER_HOSTNAME setting
        env['K8S_APISERVER_VIP'] = str(self.config['k8s_apiserver_vip'])
        env['K8S_CLUSTER_DNSNAME'] = str(self.config['k8s_cluster_dnsname'])
        env['K8S_APISERVER_HOST'] = str(self.config['k8s_apiserver_hostname'] + "." + self.config['k8s_cluster_dnsname'])

        if bool(self.config.get('global_vagrant_singlenode_lnxcluster', False)):
            logger.debug("singlenode_lnxcluster enabled")
            env['GLOBAL_VAGRANT_LNXCLP_COUNT'] = "1"
            env['GLOBAL_VAGRANT_LNXWRK_COUNT'] = "0"
            env['GLOBAL_VAGRANT_WINWRK_COUNT'] = "0"

        return env
