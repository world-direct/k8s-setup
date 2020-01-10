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
    pn_private_config = ".local/cli-config"

    def __init__(self):

        pn_current_config = Context.pn_current_config
        pn_private_config = Context.pn_private_config
        pn_conf = "./conf"
        fn_default_config="defaults.yml"
        fn_vagrant_config="vagrant.yml"

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
                            filepath if filepath != pn_current_config else os.readlink(filepath)
                        )

                        absval = os.path.relpath(os.path.join(dirname, val))
                        logger.debug("'%s' configuration rewritten to absolute path %s" % (name, absval))
                        doc[name] = absval

                # reserialize to yaml and return
                return yaml.dump(doc, Dumper=yaml.SafeDumper)

        ## Read configuration
        #############################################################
        self.config_files = []  # from lowest to highest priority
        add_config_file(os.path.join(pn_conf, fn_default_config))

        # read the current config
        if not os.path.islink(pn_current_config):
            pn_vagrantconf = os.path.abspath(os.path.join(pn_conf, fn_vagrant_config))
            logger.debug("'%s' doesnt exist, defaulting to %s" % (pn_current_config, pn_vagrantconf))
            self.set_file(pn_vagrantconf)
        
        add_config_file(pn_current_config)

        # add private config if set
        if os.path.isfile(pn_private_config):
            add_config_file(pn_private_config)

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
        
        logger.debug("Using mode '%s', inventory-file '%s'" % (self.mode, self.ansible_inventory_filepath))

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

    def set_config_value(self, name, value):
        pn_private_config = Context.pn_private_config

        vals=None

        if os.path.isfile(pn_private_config):
            with open(pn_private_config, 'r') as fs:
                content = fs.read()
                vals = yaml.load(content, Loader=yaml.SafeLoader)

        vals = {} if not vals else vals

        if value:
            logger.debug("Setting private config %s=%s" % (name, value))
            vals[name]=value
        elif vals.has_key(name):
            logger.debug("Deleting private config %s=%s" % (name, value))
            del vals[name]

        with open(pn_private_config, 'w+') as fs:
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
        env['K8S_APISERVER_HOST'] = str(self.config['k8s_apiserver_hostname'] + "." + self.config['k8s_cluster_dnsname'])

        if bool(self.config.get('global_vagrant_singlenode_lnxcluster', False)):
            logger.debug("singlenode_lnxcluster enabled")
            env['GLOBAL_VAGRANT_LNXCLP_COUNT'] = "1"
            env['GLOBAL_VAGRANT_LNXWRK_COUNT'] = "0"
            env['GLOBAL_VAGRANT_WINWRK_COUNT'] = "0"

        return env
