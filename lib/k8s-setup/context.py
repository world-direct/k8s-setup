#!/usr/bin/env python

import os
import logging
import yaml

class Context(object):

    def __init__(self):

        ## Constants
        #############################################################

        pn_current_config = os.path.expandvars("$HOME/.k8s-setup-current-config")
        pn_conf = "./conf"
        fn_default_config="defaults.yml"
        fn_vagrant_config="vagrant.yml"

        ## Read configuration
        #############################################################
        self.config_files = []  # from lowest to highest priority
        self.config_files.append(os.path.join(pn_conf, fn_default_config))

        # read the current config
        if not os.path.isfile(pn_current_config):
            logging.debug("Found %s config pointer file" % pn_current_config)
            self.config_files.append(os.path.join(pn_conf, fn_vagrant_config))
        else:
            with open(pn_current_config, 'r') as fs:
                configfile = os.path.expandvars(fs.read()).rstrip()
                logging.debug("Using %s as config file" % configfile)
                self.config_files.append(configfile)

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
        logging.info("Using mode '%s'" % self.mode)

    def get_environment(self):

        env = os.environ.copy()

        # copy each global_vagrant_* setting
        for key in self.config.keys():
            if key.startswith('global_vagrant_'):
                env[key.upper()] = str(self.config[key])

        # provide the VAGRANT_APISERVER_IP and VAGRANT_APISERVER_HOSTNAME setting
        env['K8S_APISERVER_IP'] = str(self.config['k8s_api_server_vip'])
        env['K8S_APISERVER_HOST'] = str(self.config['k8s_cluster_dnsname'])

        return env
