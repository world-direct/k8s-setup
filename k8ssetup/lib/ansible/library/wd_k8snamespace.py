#!/usr/bin/python

# RUN WITH WITH
# cd /provisioning  # this needs to be the cwd
# req='{"ANSIBLE_MODULE_ARGS":{"kubeconfig": "~/.k8s-setup/admin.conf", "namespace": "kube-global"}}'
# echo $req | python library/wd_k8snamespace.py 
#
# DEBUG WITH:
# see https://github.com/microsoft/ptvsd
# $ pip install ptvsd # ptvsc module needs to be installed
# $ python -m ptvsd --host localhost --port 5678 library/wd_helm3.py
# Attach vscode with 'Python: Remote Attach' configuration
# After "Init complete", write or paste your json input (see $req)
# press CTRL+D to close stdin
# Then the breakpoints should be stopped at

from ansible.module_utils.basic import *

import os
import sys
import json
import yaml

class ModuleFailed(Exception):
    """Exception raised for failed operation.

    Attributes:
        message -- explanation of the error
        meta -- meta return
    """

    def __init__(self, message, meta={}):
        self.message = message
        self.meta = meta


# ansible friendly log (only prints to stdout, if not redirected (by ansible?))
def log(str):
    if sys.stdout.isatty():
        print(str)


def kubectl(module, args, check_rc):
    cmd = "kubectl " + " ".join(args)

    # the helm3 rc1 don't expect kubeconfig to be quoted ("")
    log(">>> " + cmd)

    # https://docs.ansible.com/ansible/latest/reference_appendices/module_utils.html
    rc, out, err = module.run_command(cmd, use_unsafe_shell=True, check_rc=check_rc)

    log("<<<" + out)

    return (rc, out, err)


def apply_state(module):

    cargs = []
    if module.kubeconfig:
        cargs += [ "--kubeconfig", module.kubeconfig]

    # check if the namespace exists
    rc, _, _ = kubectl(module, cargs+["-o", "json", "get", "namespace", module.namespace], False)
    log("rc=" + str(rc))
    if module.state != "present":
        raise ModuleFailed("Currently only state: present is implemented")

    if rc == 0:
        # namespace exists
        return False;
    
    # create the namespace
    rc = kubectl(module, cargs+["create", "namespace", module.namespace], True)
    return True

def release_absent(module):
    meta = {}
    return False

def main():

    fields = {
        "namespace": {"required": True, "type": "str"},
        "kubeconfig": {"required": False, "type": "str"},
        "state": {
        	"default": "present", 
        	"choices": ['present'],
        	"type": 'str' 
        },
    }

    log("Init complete")
    module = AnsibleModule(argument_spec=fields)

    # reflect the params
    module.kubeconfig = module.params['kubeconfig']
    module.namespace = module.params['namespace']
    module.state = module.params['state']

    try:
        has_changed = apply_state(module)
        module.exit_json(changed=has_changed)
    except ModuleFailed as failed:
        module.fail_json(msg=failed.message)
        return

if __name__ == '__main__':
    main()