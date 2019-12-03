# General

k8s-setup provides instant access to a configured Kubernetes cluster, based
on [kubeadm](https://kubernetes.io/docs/reference/setup-tools/kubeadm/kubeadm/).
It allows to provision the cluster to a local machine as well as to production.
It is made with the help from [Ansible](https://www.ansible.com/), and 
[Vagrant](https://www.vagrantup.com/) for local virtual setup in 
[VirtualBox](https://www.virtualbox.org/).

Note: Currently only Linux is supported for local VM deployment, but it is
designed in a way, that Windows support is possible. It just needs to be implemented.

# How to use

## Install

1. Clone the repository
2. Install python (>=2.7) and pip
3. Install k8s-setup 
3. [Vagrant](https://www.vagrantup.com/intro/getting-started/install.html) (tested against Vagrant 2.2.4)
4. VirtualBox (tested against VirtualBox 6.0.12)

The steps 3. and 4. are only required, if you want to setup a local virtual cluster.

## Checkout a specific version

Use the 'k8s-setup checkout' command. You may provide a version, or omit it for
the latest version.

This will also install the required pip packages, including Ansible.
See `k8s-setup checkout --help`.

## Provide the configuration

### Local Deployment

For local vm deployments, the default 'vagrant.yml' file should work.
You don't need to provide a custom configuration, if you just want a vm cluster with a single control plane and worker node.

To access the cluster from your machine, you should have an host record for the
apiserver. The IP is configured by the `k8s_apiserver_vip` configuration setting.
The hostname is constructed by the `k8s_apiserver_hostname` and `k8s_cluster_dnsname` settings.

To generate the correct /etc/hosts file, you can run `./k8s-setup generate hostsfile --merge`.
The --merge flag instructs the generator to merge the current /etc/hosts file with
the generated records.

NOTE: Because write-access to /etc/hosts needs root permissions, you can't just
simply redirect the output to /etc/hosts. I used a temporary file, with a move
operation: `./k8s-setup generate hostsfile --merge > /tmp/hosts && sudo mv /tmp/hosts /etc/hosts`
First you should run the generator before running the provisioner, because it needs
a 'apiserver' host. After provisioning is done, run it again, so that the ingress hosts are included.

### Production Deployment

For production deployments, you need to:

1. Create an Ansible inventory file, with the machines in it.
You need to assign the host to these groups:
    * lnxclp: All Linux control plane nodes
    * lnxclp_setup: One of the Linux control plane nodes, which will be the first
    control plane instance
    * lnxwrk: All Linux worker nodes
    * winwrk: All Windows worker nodes

2. Create a .yml file, representing variables of your environment.
You can check the provided files in '/conf'. The 'default.yml' contains the 
system default settings. You can override them in your custom configuration file.

3. Register a custom configuration by executing `k8s-setup config set --file <path>`. 
The path can be absolute, or relative to the repository root. By default the
`./conf/vagrant.yml` is selected.

This Information is stored in `.local/current-config`. It is persistent, so normally you only have to execute it once.
4. You may verify if everything is ok by running `k8s-setup info`

## Provide the configuration in an own repository

k8s-setup doesn't care, where the config file is coming from. Just clone the
repository containing your configuration file, and register it by `k8s-setup config <path>`.

## Running the provisioners

By executing `k8s-setup provision` you start the provisioning process.

Because provisioning is idempotent, you can always use provision 'all'. The ability
to select a scope explicitly is just a time-saver, when you know what has hanged.
This is basically to cut wait-time when developing and testing k8s-setup.
If you don't know what has changed exacly, always provision the 'all' scope.

The following steps will be performed in the 'vagrant' mode:
1. The configuration is validated.
2. Vagrant only: The relevant configuration settings are reflected 
in environment variables.
3. Vagrant only: The `./lib/vagrant/Vagrantfile` is used to start the VMs, 
depending on the reflected environmet variables.
4. Vagrant only: The Vagrantfile declares the following provisioners:
    * Host: Updates the `/etc/hosts` files on each machine, because we have no
    DNS server in the network.
    * Ansible: Runs the `./lib/ansible/vagrant.yml` playbook. This playbook only
    performs connectivity tests. The provisioning playbooks are launched later.
    The Ansible provisioner also generates an inventory file, which is used in 
    the next step.
5. Depending on the scope, the following playbooks are executed:
    * all (default): Runs hosts, cluster and incluster playbooks.
    * hosts: Provisions the machines so that everything is installed and OS level
    configuration is applied, but no kubeadm operation to deploy the cluster was
    performed.
    * cluster: Provisions by kubeadm operations like `kubeadm init` or 
    `kubeadm join` to initialize the cluster, or add new nodes.
    * incluster: Provisions all kubernetes objects in an existing cluster.


# Vagrant Development Environment

## Networking

k8s-setup uses a default IP plan to setup the cluster network:
There is a configurable /24 network which is used for the Vagrant boxes.

```yaml
# conf/defaults.yml
global_vagrant_hosts_network: 10.0.0.*
```

You only need to change this settings, if you have conflicting IP addresses
in your LAN.

The following addresses are used:

* 10.0.0.1: Reserver (Gateway)
* 10.0.0.2: Virtual IP (keepalived) for apiserver
* 10.0.0.10-19: Control plane nodes
* 10.0.0.20-29: Linux worker nodes
* 10.0.0.30-39: Windows worker nodes
* 10.0.0.40-49: None-cluster nodes (like test-clients or AD server)

After the hosts are provisioned, you get a route by virtualbox, like:

```bash
$ ip route | grep 10.0.0.0
10.0.0.0/24 dev vboxnet3 proto kernel scope link src 10.0.0.1 
```

So you can just access the network from you host. You may add an entry in your
/etc/hosts file, like `10.0.0.2 apiserver.k8stest.local`
