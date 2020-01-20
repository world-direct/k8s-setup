#!/usr/bin/env python
from setuptools import setup, find_packages

import os

hasrepo = os.path.exists(".git")

# check if we are operating on the repo.
# if true, than we take the files and the version from the repo status
version="0.0"
if hasrepo:

    from git import Git
    repo = Git(".")

    # write VERSION.txt
    from k8ssetup import version
    version = version.getVersionFromRepo(repo)
    with open("VERSION.txt", 'w') as fs:
        fs.write(version)

    # write MANIFEST.in
    # we generate this, because we only need the files which are not gitignored
    files = repo.ls_files("lib").splitlines() + repo.ls_files("conf").splitlines() + ["VERSION.txt"]
    with open("MANIFEST.in", 'w') as fs:
        for file in files:
            fs.write("include %s\n" % file)

setup(
    name='k8s-setup',
    version=version,
    packages=find_packages(),
    url="https://github.com/world-direct/k8s-setup",
    author="gprossliner",
    author_email="createissue@github.com",
    include_package_data=True,
    install_requires=[
        'click >= 7.0',
        'ansible >= 2.8.6',
        'kubernetes >= 10.0',
        'colorlog >= 4.1.0',
        'pyyaml >= 5.2'
    ],
    setup_requires=[
        'GitPython >= 2.1.14'
    ],
    entry_points={
        "console_scripts" : [
            "k8s-setup=k8ssetup.cli:main"
        ]
    }
)