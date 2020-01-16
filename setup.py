from setuptools import setup
from k8ssetup import Info

# write MANIFEST.in
# we generate this, because we only need the files which are not gitignored
import os
with open("MANIFEST.in", 'w') as fs:
    for file in Info.getLibFiles():
        fs.write("include %s\n" % file)

setup(
    name='k8s-setup',
    version=Info.getVersion(),
    packages=['k8ssetup'],
    url="https://github.com/world-direct/k8s-setup",
    author="gprossliner",
    author_email="createissue@github.com",
    include_package_data=True,
    install_requires=[
        'click',
        'ansible >= 2.8.6',
        'argcomplete >= 1.10.0',
        'argparse >= 1.4.0',
        'kubernetes >= 10.0',
        'colorlog',
        'pyyaml >= 5.2'
    ],
    setup_requires=[
        'GitPython'
    ],
    entry_points={
        "console_scripts" : [
            "k8s-setup=k8ssetup.cli:main"
        ]
    }
)