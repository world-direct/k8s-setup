# About this provisioner

## Host-Groups

### lnxclp
Add all nodes to this group, that are control plane nodes.

### lnxclp_setup
Add any a single lnxclp node to group, that will
    - used to initialize the cluster
    - to join additional nodes to the cluster
    - to execute kubectl commands to provision the cluster

TODO: Validate there is exactly one

### lnxwkr
All linux worker nodes

### winwkr
All windows worker nodes

# Development Nodes

To check expressions in Templates, see https://jinja.palletsprojects.com/en/2.10.x/templates/#expressions


## HELM v3

Regarding Namespaces: https://github.com/helm/helm/issues/5753
