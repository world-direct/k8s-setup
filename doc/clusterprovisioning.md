# Cluster Provisioning

# Requirements

## Implement the kubeadm upgrade process
The Provisioner will validate kubernetes Version Policies, as specified
in [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade):
* No downgrade in performed
* The current minimum version is 1.16.0

## Stay online
While provisioning, we always keep a minimum number of
nodes online. The default value is '1', but this can be specified by
configuration. You should choose a number that is able to handle your 
workload.

## Interruptable Provisioning
When the provisioning is interrupted, it
should be possible to resume the operation by rerunning the provisioner.
This is only ensured, if the operation has not been interrupted in the 
middle of an external operation (like package install). But you should
always be able to reset and provision a failed Node from scratch.  

## Upgrade nodes in parallel
To optimize the provisioning execution time,
the provisioner should perform the tasks in parallel, but honor the 
minimum number of nodes

## Allow 'same version upgrade' to apply configuration changes
Because kubeadm doesn't have a 'update' command, we will handle this
by `kubeadm upgrade apply 'currentversion' --config` see:
[Support operations that need kubeadm config changes](https://github.com/world-direct/k8s-setup/issues/94) 

# Configuration Values

## k8s_version 
The 'k8s_version' configuration value (like '1.16.0') contains the 
target version of the cluster. The Cluster Provisioner performs actions,
to bring the cluster and the cluster nodes to the specified version.

## k8s_upgrade_minimum_ROLE
Specifies the minimum number of nodes for each role (lnxclp, lnxwrk, winwrk),
which should be kept online at any time.
The default value is '1' for 'Production', and '0' for 'Vagrant' mode. 

# Phases

This section outlines the implementation of the Provisioner.
As specified in the [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade) document.

Please note the following paragraph:

> You only can upgrade from one MINOR version to the next MINOR version, 
> or between PATCH versions of the same MINOR. That is, you cannot skip 
> MINOR versions when you upgrade. For example, you can upgrade from 
> 1.y to 1.y+1, but not from 1.y to 1.y+2.

The provisioner implements this by incremental upgrades until the specified 
MINOR version is reached. So if you upgrade a cluster from 1.16 to 1.18,
the provisioner upgrades the cluster to 1.17 first, and to 1.18 afterwards.

So the upgrade operation will not use the 'k8s_version' variable directly,
but will use a variable named 'k8s_upgrade_version' which will be set
dynamically from the provisioner within the Version-Loop.

As documented, we need to perform the following stages:

1. Upgrade kubeadm
2. Drain the node
3. Perform the kubeadm upgrade commands
    - First ControlPlane: `kubeadm upgrade plan` and `kubeadm upgrade apply`
    - Other Nodes: `kubeadm upgrade node`
3. Uncordon the node
4. Upgrade kubelet

Please note, that upgrade kubelet is performed after the 'Uncordon the node'
step. As restarting kubelet should not affect the current workload, we
can restart kubelet without drain / uncordon once more.

## Evaluate State

To create a provisioning plan, we need the following facts:

* current_cluster_version: This is the current version of the cluster,
taken from the 'ServerVersion' property of `kubectl version`.

This is global for a cluster, and not dependent on a specific node. 
This may also be not set, if no cluster has been provisioned yet. 
In this case, no `kubeadm upgrade`, but a `kubeadm init` will be performed. 

* kubelet_version:  `kubelet --version`

* kubeadm_version: `kubeadm version -ojson | jq ".clientVersion.gitVersion"`

### Implementation-Notes

The node specific state (kubelet and kubeadm version) will be gathered
by [Ansible custom Facts](https://medium.com/@jezhalford/ansible-custom-facts-1e1d1bf65db8).
We will deploy a 'kubelet_version.fact' and a 'kubeadm_version.fact' script 
to /etc/ansible/facts.d, so we can access them directly by 'local.kubelet_version'. 

The already implemented 'lnxkubeadm-common' role will be revisited for this purpose.

## Build the Provisioning Plan

This is the core logic of the upgrade process. The Cluster Provisioner
will dynamically create a playbook for the upgrade, containing:

### Phase 1: Cluster Initialization

If 'current_cluster_version' is unset, a 'kubeadm init' will be done.
The 'current_cluster_version' will be set after completion to the 'k8s_version'
variable.

### Phase 2: Cluster Consolidation

In this phase, we will ensure that every node is
1. joined to the cluster: This ensures that new nodes are joined
2. kubelet and kubeadm version is at least the version of the cluster

To join multiple nodes in parallel, we will use dynamic groups for this.

### Phase 3: Cluster Upgrade

If k8s_version > current_cluster_version, we will run the upgrade steps
on the first control plane. This is a serial operation.

### Phase 4: Node Upgrade

This phase is done two times, first for control-plane nodes, than for
worker-nodes.

### Phase 5: Configuration Update

If k8s_version == current_cluster_version, but the kubeadm configuration
file is different than the server version, only the kubeadm configuration
has been changed. In this case, we run the upgrade to the same version.
This implements the 'kubeadm update' workaround, like documented in the 
Requirements section.

Because we will pass the --config Argument in every kubeadm operation, 
we won't need to do this, if an upgrade has been performed before.

### Implementation-Notes
As is will be impossible to regression-test all possible combinations
of cluster version, local versions and the number of nodes, the provisioner
must implement the plan-builder so that it can be unit-tested easily.
