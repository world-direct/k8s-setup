#!/usr/bin/env python
from setuptools import setup
from k8ssetup import Info

# write MANIFEST.in
# we generate this, because we only need the files which are not gitignored
import os
with open("MANIFEST.in", 'w') as fs:
    for file in Info.getLibFiles():
        fs.write("include %s\n" % file)

    fs.write("include VERSION.txt")

# get the version information and write it into VERSION.txt
version = Info.getVersion()
with open("VERSION.txt", 'w') as fs:
    fs.write(version)

setup(
    name='k8s-setup',
    version=version,
    packages=['k8ssetup'],
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