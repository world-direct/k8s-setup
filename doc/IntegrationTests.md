# Integration Tests

This file describes Integration Tests, that may get implemented later.
After we have the priorities assigned to implement the Integration Tests,
we can check this document to priorize and implement Integratio Tests.

## IT1: Setup cluster with default Configuration

This test will provision a cluster with distinct control plane and linux worker
nodes.

Ensures:
- Provisioning runs without errors
- API Server is listening
- All nodes are online

## IT1: Sub-Tests

The Sub-Tests are based on the previous setup, runs additional checks:

- Ingress is bound to 'k8s_loadbalancers_ingress_ip'
- Services can be of type LoadBalancer
- wd-nginx-test application can be browsed using the ingress-rule
- The cluster is operational if machines are restarted (tests #73)
- New clp nodes can be joined after cluster afterwards (tests #74)


## IT1: Test cluster overall availablility when machines die

This test will use a cluster with three control plane, and two worker nodes.
A service (like wd-nginx-test) is deployed on the cluster, when the following
events happen:

- a control plane node is disconnected from network
- a control plane node is restarted
- a worker node is disconnected from network
- a worker node is restarted

Ensures:
- The service is available with an outage of max. 10 seconds.

# Features considered "untestable"

The features below can't be tested in because of resource availablilty:

## Trident Configuration

Because we have no ontap-nas in the pipeline runner, we can't test Dynamic 
Volume Provisioning with the Trident configuration.