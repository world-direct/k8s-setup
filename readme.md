# VM CONFIGURATION

For the nodes to communicate, we create a "NodeNetwork"
   10.0.0.0/24

The first master has: 10.0.0.1
Next masters:         10.0.0.2, 10.0.0.3
Master virtual IP:    10.0.0.10
Workers:              10.0.0.11-10.0.0.254

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