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

# Install git and clone the 'k8s-setup' repository

```bash
cd ~
$repo=https://ads.world-direct.at/Company/Technology/_git/k8s-setup
git clone $repo
cd k8s-setup
```

# Checkout the current version

The current version is v0.0.1, so the command should be

```bash
cd ~/k8s-setup
git fetch && git fetch tags
git checkout v0.0.1
```

# Modify the playbook vars to match desired configuration

This is documented in the configuration-file itself:
provisioning/group_vars/all.yml

# Run ansible-playbook

https://docs.ansible.com/ansible/2.4/playbooks.html


```bash
cd ~/k8s-setup/provisioning
ansible-playbook hostplaybook.yml 
```

