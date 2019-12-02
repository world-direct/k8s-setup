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


# Features considered "untestable"

The features below can't be tested in because of resource availablilty:

## Trident Configuration

Because we have no ontap-nas in the pipeline runner, we can't test Dynamic 
Volume Provisioning with the Trident configuration.