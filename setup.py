from setuptools import setup

setup(
    name='k8s-setup',
    version='0.1',
    py_modules=['k8ssetup'],
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points={
        "console_scripts" : [
            "k8s-setup=k8ssetup.cli:main"
        ]
    }
)