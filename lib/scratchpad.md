
# VM CONFIGURATION

For the nodes to communicate, we create a "NodeNetwork"
   10.0.0.0/24

```
The first master has: 10.0.0.1
Next masters:         10.0.0.2, 10.0.0.3
Master virtual IP:    10.0.0.10
Workers:              10.0.0.11-10.0.0.254
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


# run standalone

```sh
# full cmdline executed by vagrant
ansible-playbook \
    --connection=ssh \
    --timeout=30 \
    --limit=all,localhost \
    --inventory-file=../vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory \
    --extra-vars={\"k8s_api_server_vip\":\"10.0.0.2\",\"k8s_cluster_dnsname\":\"k8stest.local\",\"k8s_apiserver_hostname\":\"apiserver\",\"k8s_enable_proxy\":true,\"host_primary_interface_name\":\"eth1\"} \
    --become \
    --ssh-extra-args='-o StrictHostKeyChecking=no' \
    -e@../../conf/vagrant.yml \
    vagrant.yml

# minimum cmdline to execute vagrant.yml
ansible-playbook \
    --inventory-file=../vagrant/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory \
    --ssh-extra-args='-o StrictHostKeyChecking=no' \
    -e@../../conf/vagrant.yml \
    vagrant.yml


```

# Install ansible

https://docs.ansible.com/ansible/2.4/intro_installation.html

You should install by pip, to ensure, that you get the 2.7.12 version.
The playbook validates that it is a 2.7.* version.


# Create the inventory file

https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html

To test the connectivity-parameters, you can use the 'ansible' cmdline:
https://docs.ansible.com/ansible/2.4/ansible.html

The default location is '/etc/ansible/hosts'


```
# List all machines, with there connectivity-parameters
# https://docs.ansible.com/ansible/2.4/intro_inventory.html#list-of-behavioral-inventory-parameters
lnxwrk1 ansible_host=127.0.0.1 ansible_port=2201 ansible_user='vagrant' ansible_ssh_private_key_file='...'
lnxclp1 ansible_host=127.0.0.1 ansible_port=2222 ansible_user='vagrant' ansible_ssh_private_key_file='...'

# The [lnxclp_setup] group must contain exactly one of the clp nodes
# This is only special about how the provisioning is done
# The [lnx-clp-setup] node inits the cluster, while the [lnxclp] nodes join the cluster
# as additional control plane nodes
[lnxclp_setup]
lnxclp1

# The [lnxclp] group contains all nodes which run the control-plane.
# This INCLUDES the node specified in lnxclp_setup
[lnxclp]
lnxclp1

# The [lnxwrk] group contains all nodes which join the cluster as linux workers
[lnxwrk]
lnxwrk1

# The [winwrk] group contains all nodes which join the cluster as windows workers
# There must be a winrm connection configured to the windows nodes
[winwrk]

# These vars are static, and should not be changed.
[winwrk:vars]
ansible_winrm_scheme=http
ansible_become=false

```

# Test the connectivity

```
# ping the control-pipe
ansible all -m ping

# execute a ad-hoc command
ansible all -a "/bin/echo hello"
```

# Checkout the current version

The current version is v0.0.1, so the command should be

```bash
cd ~/k8s-setup
git fetch && git fetch tags
git checkout v0.0.1
```
