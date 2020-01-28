import os

import logging
logger = logging.getLogger(__name__)

def getVersion():

    """
    If the package is no repository, the setuptools version is returned

    If we are in "Development Mode" (pip install --editable), and have a 
    Git Repository, the version determinated by the git repository status
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
    * 0.1.dev => Directly on a tag "v0.1-alpha", but tag is prelease according to semver (like '-alpha' here)
    * 0.1.dev0+bb231b5x => Latest tag was "v0.1", 0 commits ahead, commitid = bb231b5, dirty tree
    * 0.1.dev4+ca6992 => Latest tag was "v0.1", 4 commits ahead, commitid = ca6992f
    * 0.1.dev4+ca6992x => Latest tag was "v0.1", 4 commits ahead, commitid = ca6992f, dirty tree

    """

    hasrepo = os.path.exists(".git") or os.path.exists("../.git")
    if hasrepo:
        from git import Git
        repo = Git(".")
        return getVersionFromRepo(repo)

    with open("./VERSION.txt", 'r') as fs:
        version = fs.readline()
        return version


def getVersionFromRepo(repo):

    raw=repo.describe("--tags", "--dirty", "--long", "--match", 'v*')
    logger.debug("raw version from 'git describe': %s" % raw)

    # we are not directly on a 'v' tag, so this is not a public release
    parts = raw.split('-')
    dirty = parts[len(parts)-1] == "dirty"
    if dirty:
        logger.debug("popped 'dirty'")
        parts.pop()

    sha = parts.pop().lstrip("g")
    logger.debug("popped 'commit-id': %s" % sha)

    nahead = int(parts.pop())
    logger.debug("popped 'commits ahead': %s" % nahead)

    tag = "-".join(parts).lstrip("v")
    logger.debug("popped 'tag': v%s" % tag)

    tagversion = tag.split("-")[0]
    logger.debug("get 'tagversion': %s" % tagversion)

    primaryversion = tagversion

    tagtext = "" if tag == tagversion else tag[len(tagversion)+1:]
    if tagtext:
        logger.debug("remaining 'tagtext': %s => .dev version" % tagtext)

    version = primaryversion

    if dirty:
        version += ".dev%s+%sX" % (nahead, sha)
        logger.debug("We are dirty, so use the long output: %s" % version)
        return version

    if nahead:
        version += ".dev%s+%s" % (nahead, sha)
        logger.debug("We are ahead of the tag, so use the long output: %s" % version)
        return version

    if tagtext:
        version += ".dev0"
        logger.debug("We are on a prelease tag, so use .dev0 version: %s" % version)
        return version
