#!/usr/bin/env python

import os
import sys
import logging
import yaml

logger = logging.getLogger(__name__)

class Context(object):


    ## Constants
    #############################################################

    pn_current_config = ".local/current-config"

    def __init__(self):

        pn_current_config = Context.pn_current_config
        pn_conf = "./conf"
        fn_default_config="defaults.yml"
        fn_vagrant_config="vagrant.yml"

        ## Read configuration
        #############################################################
        self.config_files = []  # from lowest to highest priority
        self.config_files.append(os.path.join(pn_conf, fn_default_config))

        # read the current config
        if not os.path.islink(pn_current_config):
            pn_vagrantconf = os.path.abspath(os.path.join(pn_conf, fn_vagrant_config))
            logger.debug("'%s' doesnt exist, defaulting to %s" % (pn_current_config, pn_vagrantconf))
            self.set_file(pn_vagrantconf)
        
        logger.debug("'%s' --> '%s'" % (pn_current_config, os.readlink(pn_current_config)))
        self.config_files.append(pn_current_config)

        # TODO: check if all self.config_files exists

        # To apply defaults, we make a very simple merge, that combines the content
        # of the file in the right order, and then feed it to yaml.load
        # Yaml ignores redefined mappings, so merged file need to be sorted from
        # highest to lowest priority. 'defaults.yml' is the last one
        self.config_string = ""
        for config_file in self.config_files:
            with open(config_file, 'r') as fs:
                self.config_string = self.config_string + fs.read()

        self.config = yaml.load(self.config_string, Loader=yaml.SafeLoader)

        # TODO: check if global_mode exists, and if it is 'vagrant' or 'production'
        self.mode = self.config['global_mode']
        self.ansible_inventory_file = self.config['ansible_inventory_file']
        logger.debug("Using mode '%s'" % self.mode)

    def set_file(self, filepath):

        localpath=os.path.dirname(Context.pn_current_config)
        if not os.path.isdir(localpath):
            os.mkdir(localpath)

        if not os.path.isfile(filepath):
            print("File '%s' not found. Exiting" % filepath)
            exit(1)

        if os.path.islink(Context.pn_current_config):
            logger.debug("'%s' exist. Removing" % (Context.pn_current_config))
            os.remove(Context.pn_current_config)

        logger.debug("Creating symlink '%s' --> '%s'" % (Context.pn_current_config, filepath))
        os.symlink(filepath, Context.pn_current_config)

    def get_environment(self):

        env = os.environ.copy()

        # copy each global_vagrant_* setting
        for key in self.config.keys():
            if key.startswith('global_vagrant_'):
                env[key.upper()] = str(self.config[key])

        # provide the VAGRANT_APISERVER_IP and VAGRANT_APISERVER_HOSTNAME setting
        env['K8S_APISERVER_VIP'] = str(self.config['k8s_apiserver_vip'])
        env['K8S_APISERVER_HOST'] = str(self.config['k8s_apiserver_hostname'] + "." + self.config['k8s_cluster_dnsname'])

        return env
