#!/usr/bin/python

# RUN WITH WITH
# cd /provisioning  # this needs to be the cwd
# req='{"ANSIBLE_MODULE_ARGS":{"kubeconfig": "~/k8stest.local/admin.conf","chart": "charts/wd-flannel","namespace": "kube-global"}}'
# echo $req | python library/wd_helm3.py 
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

class HelmChart:

    def __init__(self, name, appversion, description, type, version):
        self.name = name
        self.appversion = appversion
        self.description = description
        self.type = type
        self.version = version

class HelmRelease:

    def __init__(self, name, namespace, revision, updated, status, chartname, appversion):
        self.name = name
        self.namespace = namespace
        self.revision = revision
        self.updated = updated
        self.status = status
        self.chartname = chartname
        self.appversion = appversion

class HelmBase:

    """Class implementing controlling the Helm(3) cli

    Attributes:
        runhelmfn -- function called to execute the helm tool (executorfn(args) => (returncode int, stdout str, stderr str))
        logfn -- log(str)
        kubeconfig -- str with kubeconfig file to use
    """

    def __init__(self, runhelmfn, logfn, kubeconfig):
        self.kubeconfig = kubeconfig
        self.__runhelm = runhelmfn
        self.__log = logfn

    def __helm(self, args):

        if self.kubeconfig:
            args.append("--kubeconfig")
            args.append(self.kubeconfig)

        rc, stdout, strerr = self.__runhelm(args)
        return stdout

    def __helmyaml(self, args):
        args.append("--output")
        args.append("yaml")

        res = self.__helm(args) # + " --output json")
        return yaml.load(res, Loader=yaml.BaseLoader)

    def list(self, namespace):
        res = self.__helmyaml(["--namespace", namespace, "list"])

        def release(r):
            return HelmRelease(r['Name'], r['Namespace'], r['Revision'], r['Updated'], r['Status'], r['Chart'], r['AppVersion'])

        return map(release, res)

    def listone(self, namespace, name):
        for rel in self.list(namespace):
            if rel.name == name:
                return rel

        return None

    def showchart(self, chart):
        res = self.__helm(["show", "chart", chart])
        r = yaml.load(res, Loader=yaml.BaseLoader)

        # Construct return object
        obj = HelmChart(r['name'], r['appVersion'], r['description'], r['type'], r['version'])

        return obj;

    def install(self, name, chartname, namespace):
        res = self.__helm(["--namespace", namespace, "install", name, chartname])
        self.__log(res)


# ansible friendly log (only prints to stdout, if not redirected (by ansible?))
def log(str):
    if sys.stdout.isatty():
        print(str)


class HelmAnsible(HelmBase):

    def __log(self, str):
        log(str)  # call global log function

    def __runhelmfn(self, args):
        cmd = "helm3 " + " ".join(args)

        # the helm3 rc1 don't expect kubeconfig to be quoted ("")
        self.__log(">>> " + cmd)

        # https://docs.ansible.com/ansible/latest/reference_appendices/module_utils.html
        rc, out, err = self.module.run_command(cmd, use_unsafe_shell=True, check_rc=True)

        self.__log("<<<" + out)

        return (rc, out, err)

    def __init__(self, module, kubeconfig):
        self.module = module

        def runhelm(args):
            return self.__runhelmfn(args)

        def log(str):
            self.__log(str)

        HelmBase.__init__(self, runhelm, log, kubeconfig)


def release_present(module):

    helm = HelmAnsible(module, module.kubeconfig)

    # find the chart directory
    chartpath = module.params['chart']
    if not os.path.exists(chartpath):
        raise ModuleFailed("chart not found")

    # get chart info
    chart = helm.showchart(chartpath)

    # if unnamed, the name is the name of the chart
    name = module.name
    if not name:
        name = chart.name

    # get releases
    release = helm.listone(module.namespace, name)

    if not release:
        log("INSTALL CHART")
        helm.install(name, chartpath, module.namespace)

        return True # no release for this chart
    
    if release.appversion != chart.appversion:
        log("PERFORM UPDATE")
        return True

    # already installed
    return False


    return False

def release_absent(module):
    meta = {}
    return False

def main():

    fields = {
        "chart": {"required": True, "type": "str"},
        "name": {"required": False, "type": "str" },
        "namespace": {"required": False, "type": "str"},
        "kubeconfig": {"required": False, "type": "str"},
        "state": {
        	"default": "present", 
        	"choices": ['present', 'absent'],
        	"type": 'str' 
        },
    }

    choice_map = {
        "present": release_present,
        "absent": release_absent
    }

    log("Init complete")
    module = AnsibleModule(argument_spec=fields)

    # reflect the params
    module.kubeconfig = module.params['kubeconfig']
    module.namespace = module.params['namespace']
    module.name = module.params['name']

    try:
        fn = choice_map.get(module.params['state'])
        has_changed = fn(module)
        module.exit_json(changed=has_changed)
    except ModuleFailed as failed:
        module.fail_json(msg=failed.message)
        return

if __name__ == '__main__':
    main()