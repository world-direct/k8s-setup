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
