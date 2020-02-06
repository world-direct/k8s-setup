#!/usr/bin/python

# RUN WITH WITH
# cd /provisioning  # this needs to be the cwd
# req='{"ANSIBLE_MODULE_ARGS":{"kubeconfig": "~/.k8s-setup/admin.conf","chart": "charts/wd-flannel","namespace": "kube-global"}}'
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

from ansible.module_utils.basic import AnsibleModule

import os
import sys
import json
import yaml
import tempfile

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

    def __init__(self, source, name, appversion, description, type, version):
        self.source = source
        self.name = name
        self.appversion = appversion
        self.description = description
        self.type = type
        self.version = version
        self.versionedname = name + "-" + version

class HelmRelease:

    def __init__(self, name, namespace, revision, updated, status, chartname, appversion):
        self.name = name
        self.namespace = namespace
        self.revision = revision
        self.updated = updated
        self.status = status
        self.versionedchartname = chartname
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

        _, stdout, _ = self.__runhelm(args)
        return stdout

    def __helmyaml(self, args):
        args.append("--output")
        args.append("yaml")

        res = self.__helm(args) # + " --output json")
        return yaml.load(res, Loader=yaml.BaseLoader)

    def list(self, namespace):
        res = self.__helmyaml(["--namespace", namespace, "list"])

        def release(r):
            return HelmRelease(r['name'], r['namespace'], r['revision'], r['updated'], r['status'], r['chart'], r['app_version'])

        return map(release, res)

    def listone(self, namespace, name):
        for rel in self.list(namespace):
            if rel.name == name:
                return rel

        return None

    def loadchart(self, chartsource):
        res = self.__helm(["show", "chart", chartsource])
        r = yaml.load(res, Loader=yaml.BaseLoader)

        # Construct return object
        obj = HelmChart(chartsource, r['name'], r.get('appVersion'), r.get('description'), r.get('type'), r['version'])

        return obj

    def valuesfile(self, name, values, args):
        """
        Creates or updates the valuesfile.
        Returns: (dirty)
        Appends -f <filename> to args
        """

        dirty = False
        valuesblob = values.encode("utf-8")

        # check if the directory for the values files exist
        valuesdir=os.path.expanduser("~/.k8s-setup/helm")
        if not os.path.isdir(valuesdir): os.mkdir(valuesdir)

        # check the file
        valfilename = os.path.join(valuesdir, name)
        if not os.path.isfile(valfilename):
            dirty = True
        else:
            
            import hashlib

            # check MD5 of existing file changes
            md5hash = hashlib.md5()
            with open(valfilename, 'rb') as valfile:
                blob = valfile.read()
                md5hash.update(blob)
                filemd5 = md5hash.hexdigest()
                self.__log("Hash of %s: %s" % (valfilename, filemd5))

            # check MD5 of values
            md5hash = hashlib.md5()
            md5hash.update(valuesblob)
            valuesmd5 = md5hash.hexdigest()

            self.__log("Hash of values: %s" % (valuesmd5))

            dirty = filemd5 != valuesmd5

        if dirty:
            with open(valfilename, "w") as valfile:
                valfile.writelines(values)
                valfile.flush()

        args.append("-f")
        args.append(valfilename)

        return dirty


    def install(self, name, chart, namespace, atomic, values=None):
        args = ["--namespace", namespace, "install", name, chart.source]

        if atomic:
            args.append("--atomic")

        if values:
            self.valuesfile(name, values, args)

        res = self.__helm(args)
        self.__log(res)

    def upgrade(self, release, chart, values):
        args = ['-n', release.namespace, 'upgrade', release.name, chart.source]

        if values:
            self.valuesfile(release.name, values, args)

        res = self.__helm(args)
        self.__log(res)

    def updateifdirty(self, release, chart, values):
        args = ['-n', release.namespace, 'upgrade', release.name, chart.source]

        if values:
            if self.valuesfile(release.name, values, args):
                self.__log("VALUES CHANGED")
                res = self.__helm(args)
                self.__log(res)
                return True

        return False

    def uninstall(self, release):
        res = self.__helm(["--namespace", release.namespace, "uninstall", release.name])
        self.__log(res)

# ansible friendly log (only prints to stdout, if not redirected (by ansible?))
def log(str):
    if sys.stdout.isatty():
        print(str)


class HelmAnsible(HelmBase):

    # pylint: disable=method-hidden
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


def apply_state(module):

    helm = HelmAnsible(module, module.kubeconfig)

    # find the chart directory
    chartpath = module.params['chart']
    if not os.path.exists(chartpath):
        raise ModuleFailed("chart not found")

    # get chart info
    chart = helm.loadchart(chartpath)

    # if no nave is given, the name is the name of the chart
    releasename = module.name
    if not releasename:
        releasename = chart.name

    # get the release
    release = helm.listone(module.namespace, releasename)

    if(module.state == "present"):

        if not release:
            log("INSTALL CHART")
            helm.install(releasename, chart, module.namespace, module.atomic, module.values)

            return True # no release for this chart
        
        if release.appversion != chart.appversion or release.versionedchartname != chart.versionedname:
            log("PERFORM UPDATE")
            helm.upgrade(release, chart, module.values)
            return True
        else:
            return helm.updateifdirty(release, chart, module.values)

        # already installed
        return False
    elif (module.state == "absent"):
        log("PEROFRM UNINSTALL")
        helm.uninstall(release)
        return True
    else:
        raise ModuleFailed("Invalid state value '%s'" % module.state)


    return False

def release_absent(module):
    return False

def main():

    fields = {
        "chart": {"required": True, "type": "str"},
        "name": {"required": False, "type": "str" },
        "namespace": {"required": False, "type": "str"},
        "kubeconfig": {"required": False, "type": "str"},
        "atomic": {"default": False, "type": "bool"},
        "values": {
            "required": False,
            "type": "json"
        },
        "state": {
        	"default": "present", 
        	"choices": ['present', 'absent'],
        	"type": 'str' 
        },
    }

    log("Init complete")
    module = AnsibleModule(argument_spec=fields)

    # reflect the params
    module.kubeconfig = module.params['kubeconfig']
    module.namespace = module.params['namespace']
    module.name = module.params['name']
    module.state = module.params['state']
    module.values = module.params['values']
    module.atomic = module.params['atomic']

    try:
        has_changed = apply_state(module)
        module.exit_json(changed=has_changed)
    except ModuleFailed as failed:
        module.fail_json(msg=failed.message)
        return

if __name__ == '__main__':
    main()