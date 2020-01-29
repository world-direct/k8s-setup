#!/usr/bin/env python
import os

class Paths(object):
    """ Constants for paths used in provisioning"""

    src_confroot = "./conf"
    src_confdefaults = src_confroot + "/defaults.yml"
    src_confvagrant = src_confroot + "/vagrant.yml"
    src_libroot = "./lib"
    src_vagrantfile = src_libroot + "/vagrant/Vagrantfile"
    src_vagrantpp = src_libroot + "/ansible/vagrantpp.yml"

    sys_homedir = os.path.expanduser("~")
    sys_homeroot = sys_homedir + "/.k8s-setup"
    sys_currentconfig = sys_homeroot + "/current-config"
    sys_cliconfig = sys_homeroot + "/cli-config"
    sys_cacrt = sys_homeroot + "/cacrt.pem"
    sys_cakey = sys_homeroot + "/cakey.pem"

    sys_vagrantfile = sys_homeroot + "/Vagrantfile"
    sys_vagrantpp = sys_homeroot + "/vagrantpp.yml"
    sys_vagrantgeneratedinventory = os.path.dirname(sys_vagrantfile) + \
        "/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory"
