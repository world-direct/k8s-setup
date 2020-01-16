import logging
import subprocess
import os
import yaml
import re

logger = logging.getLogger()

from context import Context

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
        version = Info.getVersion()
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

        out = yaml.dump(vals, Dumper=yaml.SafeDumper)
        output.write(out)

    @classmethod
    def getGitRepo(cls):
        # this is a setup_requires dependency
        from git import Git
        repo = Git(".")
        return repo


    @classmethod
    def getVersion(cls):
        """
        Returns the version determinated by the git repository status
        It is determinated by git describe --tags, using the v* tags

        Format:
        X.Y[.'dev'N+ID]['x']
        X = major version
        Y = minor version
        N = commits ahead of tag
        ID = commitid
        x = dirty tree

        Cases:
        * 0.1 => Directly on a tag "v0.1"
        * 0.1.dev0+bb231b5x => Latest tag was "v0.1", 0 commits ahead, commitid = bb231b5, dirty tree
        * 0.1.dev4+ca6992 => Latest tag was "v0.1", 4 commits ahead, commitid = ca6992f
        * 0.1.dev4+ca6992x => Latest tag was "v0.1", 4 commits ahead, commitid = ca6992f, dirty tree

        """

        # versionsh = os.path.abspath(os.path.join(os.path.dirname(__file__), "../version.sh"))
        # logger.debug("using script %s" % versionsh)
        # version=subprocess.check_output(versionsh).strip()
        # return version[1:]

        repo = Info.getGitRepo()

        raw=repo.describe("--tags", "--dirty", "--long", "--match", 'v*')
        print(raw)


        # we are not directly on a 'v' tag, so this is not a public release
        parts = raw.split('-')
        dirty = parts[len(parts)-1] == "dirty"
        if dirty:
            parts.pop()

        sha = parts.pop().lstrip("g")
        nahead = parts.pop()
        tag = "-".join(parts).lstrip("v")
        tagversion = tag.split("-")[0]
        tagtext = "" if tag == tagversion else tag[len(tagversion)+1:]

        version = tagversion

        if dirty or nahead > 0:
            # long output
            version += ".dev%s+%s" % (nahead, sha)

        if(dirty):
            version = version + "x"

        print(version)
        return version

        
    @classmethod
    def getLibFiles(cls):
        """Returns a list of files to include in setup"""
        files = Info.getGitRepo().ls_files("lib").splitlines()
        return files
