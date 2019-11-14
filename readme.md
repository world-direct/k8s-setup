# General

k8s-setup provides instant access to a configured kubernetes Cluster, based
on [kubeadm](https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm/).
It allows to provision the cluster to a local machine, and production.
It is with the help from [Ansible](https://www.ansible.com/), and 
[Vagrant](https://www.vagrantup.com/) for local virtual setup in 
[VirtualBox](https://www.virtualbox.org/)

Note: Currently only Linux is supported for local VM deployment, but it is
designed in a way, that Windows support is possible. It just need to be implemented.

# How to use

## Install

1. Clone the repository
2. Install python (>=2.7) and pip
3. Install k8s-setup 
3. Vagrant (tested against Vagrant 2.2.4)
4. VirtualBox (tested against VirtualBox 6.0.12)

The steps 3. and 4. is only required, if you want to setup a local virtual cluster.

## Checkout a specific version

Use the 'k8s-setup checkout' command. You may provide a version, or omit it for
the latest version.

This will also install the required pip packages, including Ansible.
See `k8s-setup checkout --help`.

## Provide the configuration

For local vm deployments, the default 'vagrant.yml' file should work.
You don't need to do anything, if you just want a vm cluster with a single control plane and worker node.

For production deployments, you need to 

1. Create an ansible inventory file, with the machines in it.
You need to assign the host to these groups:
    * lnxclp: All Linux control plane nodes
    * lnxclp_setup: One of the linux control plane nodes, which will be the first
    control plane instance.
    * lnxwrk: All Linux worker nodes
    * winwrk: All Windows worker nodes

2. Create a .yml file, representing variables of your envrionment.
You can check the provided files in '/conf'. The 'default.yml' contains the 
system default settings. You can override them in your custom configuration file.

3. Activate the configuration by executing `k8s-setup config <path>`. 
The path can be absolute, or relative to the repository root. By default the
`./conf/vagrant.yml` is selected.

This Information is stored `.local/current-config`. This is persistent, so normally you only have to execute in once.
4. You may verify everything by running `k8s-setup info`

## Provide the configuration in an own repository

k8s-setup doesn't care, where the config file is comming from. Just clone the
repository containing your configuration file, and register it by `k8s-setup config <path>`

## Running the provisioners

By executing `k8s-setup provision` you start the provisioning process.

Because provisioning is idempotent, you can always use provision all. The ability
to select a scope explicitly is just a time-saver, when you know what has hanged.
This is basically to cut wait-time when developing and testing k8s-setup.
If you don't know what has changed exacly, always provision the 'all' scope.

The following steps will be performed in the 'vagrant' mode:
1. The configuration is validated
2. Vagrant only: The relevant configuration Settings are reflected 
in Environment-Variables.
3. Vagrant only: The `./lib/vagrant/Vagrantfile` is used to start the VMs, 
depending on the reflected Environmnet-Variables.
4. Vagrant only: The Vagrantfile declares the following provisioners:
    * Host: Updates the `/etc/hosts` files on each machine, because we have no
    DNS Server in the network
    * Ansible: Runs the `./lib/ansible/vagrant.yml` playbook. This playbook only
    performs connectivity tests. The provisioning playbooks are lauched later.
    The Ansible Provisioner also generates an inventory file, which is used in 
    the next step.
5. Depending on the scope, the following playbooks are executed
    * all (default): Runs hosts, cluster and incluster playbooks
    * hosts: Provisions the machines so that everything is installed and OS level
    configuration is applied, but no kubeadm operation to deploy the cluster has
    performed.
    * cluster: Provisions by kubeadm operations like `kubeadm init` or 
    `kubeadm join` to initialize the cluster, or add new nodes
    * incluster: Provisions all kubernetes objects in an existing cluster
