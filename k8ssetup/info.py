import logging
import subprocess
import os
import re

logger = logging.getLogger()

from .context import Context
from .version import getVersion

class Info:

    def __init__(self, context):
        self.context = context

    def run(self, output):
        logger.debug('cmd:info()')

        context = self.context

        # It would be way better to preserve insertion order
        # For python, you have to use a 'collections.OrderedDict' object
        # But pyyaml 5.2 (installed with pip) don't handle OrderDict.
        # This should work and is documented, and also implemented in source:
        # https://github.com/yaml/pyyaml/blob/5.2/lib3/yaml/representer.py#L358
        # But when debugging, the file is different. This seems more a pip issue. 
        # TODO: Fix ordering
        vals = dict()

        # version
        version = getVersion()
        vals["version"] = version

        # config metadata
        vals["config-files"] = context.config_files

        # important configuration values
        conf = dict()
        vals["configuration"] = conf
        conf["mode"] = context.mode
        conf["cluster-dns-name"] = context.config["k8s_cluster_dnsname"]
        conf["ansible_inventory_filepath"] = context.ansible_inventory_filepath
        conf["k8s-version"] = context.config["k8s_version"]

        if context.mode == "vagrant":
            conf["lnxclp-nodes"] = context.config["global_vagrant_lnxclp_count"]
            conf["lnxwrk-nodes"] = context.config["global_vagrant_lnxwrk_count"]
            conf["winwrk-nodes"] = context.config["global_vagrant_winwrk_count"]

        import yaml
        out = yaml.dump(vals, Dumper=yaml.SafeDumper)
        output.write(out)
