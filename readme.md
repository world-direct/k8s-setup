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
2. Create a .yml file, representing variables of your envrionment.
You can check the provided files in '/conf'. The 'default.yml' contains the 
system default settings. You can override them in your custom configuration file.
3. Activate the configuration by executing `k8s-setup config <path>`. 
The path can be absolute, or relative to the repository root. By default the
`./conf/vagrant.yml` is selected.
This Information is stored ~/.k8s-setup-current-config. This is in your home directory, so normally you only have to execute in once.
4. You may verify everything by running `k8s-setup info`

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
    * Ansible: Runs the `./lib/ansible/hosts.yml` playbook. This playbook only
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

# VM CONFIGURATION

For the nodes to communicate, we create a "NodeNetwork"
   10.0.0.0/24

The first master has: 10.0.0.1
Next masters:         10.0.0.2, 10.0.0.3
Master virtual IP:    10.0.0.10
Workers:              10.0.0.11-10.0.0.254

# how to use vagrant here

Vagrant is configured to run the ansible provisioner without --limit (see Vagrantfile).
To avoid, that vagrant will run this (for all) on all hosts, seperate starting
the VMs from provisioning:

```sh

# startup Vagrant boxes
vagrant up --no-provision

# first provision with 'host' provider, to ensure we have /etc/hosts
# in production, this will be an DNS server
vagrant provision --provision-with hosts

# provision the entire cluster
# the loop is still present, so you have to CTRL+C when the first host is done :(
vagrant provision


```

# Single Master

For the first version, we use a single master, we will create a VIP later on.

# references

https://github.com/oracle/vagrant-boxes/blob/master/Kubernetes/Vagrantfile

# test ansible without vagrant

```sh
ansible winwrk1 -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory -m win_ping
# if you get SSL_WRONG_VERSION_NUMBER, read https://github.com/hashicorp/vagrant/issues/10765
# you may set this manually by now
```

# winrt SSL_WRONG_VERSION_NUMBER



After setting `ansible_winrm_scheme=http` in the vagrant_ansible


# setup winrt for python

```sh
pip install "pywinrm>=0.3.0"

# if this fails with 'Segmentation fault (core dumped)' run
sudo apt remove python-cryptography
```


# to install the controller

```
yum install bash-completion
source <(kubectr completion bash)
```



# run standalone

ansible-playbook \
    --connection=ssh \
    --timeout=30 \
    --limit=all,localhost \
    --inventory-file=./lib/vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory \
    --extra-vars={\"k8s_api_server_vip\":\"10.0.0.2\",\"k8s_cluster_dnsname\":\"k8stest.local\",\"k8s_apiserver_hostname\":\"apiserver\",\"k8s_enable_proxy\":true,\"host_primary_interface_name\":\"eth1\"} \
    --become \
    --ssh-extra-args='-o StrictHostKeyChecking=no' \
    -e@conf/vagrant.yml \
    lib/ansible/utils.yml
    
