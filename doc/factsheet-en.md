---
theme : "moon"
transition: "slide"
highlightTheme: "monokai"
logoImg: "https://github.com/kubernetes/kubernetes/raw/master/logo/logo.png"
slideNumber: false
title: "World-Direct k8s-setup"
center: false
---

<style type="text/css">
  .reveal p {
    text-align: left;
    font-size: 14pt;
  }
</style>

## **k8s-setup**

*This document describes the k8s-setup project, to automatically install and manage a kubernetes cluster*

guenter.prossliner@world-direct.at

02.03.2020

---

# Introduction

World-Direct has desides to use [Kubernetes](https://www.kubernetes.io) to 
manage it's Container based Services.

The "k8s-setup" is an opensourced project, that needs to implement the 
following requirements:

---

## Hybrid Kubernetes Cluster I

We will use Kubernetes for these kinds of applications:

* Own Windows applications: In most cases, there are applications written for
the full .NET Framework. These depend on IIS, may contain Windows Services, and 
use Windows specific Features like Event-Viewer, Performance-Counters or the Task-
Scheduler.

* Own .NET Core applications: New projects are developed for .NET Core by default.
There may be hosted in Windows or Linux. When there are no specific technical or
organizational dependencies on a Windows host, we will host them in Linux containers.

* Third-Party Applications: There are applications which have existing Docker 
Images. An example would be an Elastic-Search Instance, or a Wordpress Site 
with it's database. Most of these Images run in an Linux host.

---

## Hybrid Kubernetes Cluster II

Given the different kinds of applications, we need to support both: Windows- and 
Linux-Containers. This Setup is called "Hybrid Cluster" in Kubernetes.

Nodes can be added as needed. You just have to list them in the Ansible 
inventory, and run the provisioning tool.

Our current configuration runs three Linux Nodes, which run the "Control Plane" 
role. These are the "Controller" or "Master" nodes.

The starting configuration defines three Linux and Windows Worker nodes.

---

## Active Directory Authentication

Kubernetes doesn't implement a User-Management, but supports implementations for
external User-Management tools. We use the LDAP Module from [dex](https://github.com/dexidp/dex),
to issue [OpenID Connect Tokens](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens).

This configuration allows Users to authenticate by their Active-Directory Domain
Credentials. These can be used to authenticate to the Kubernetes dashboard, or to
configure a local [kubectl Context](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/#define-clusters-users-and-contexts)
to use the Kubernetes API or Kubernetes CLI Tools.

To avoid authorizing individual Users, dex is configured to include Group 
Membership information for predefined Active-Directory Groups, which are used
to create Role-Bindings in Kubernetes.

---

## Access Control and Project Isolation

A single Kubernetes Cluster will be used by different Organization Units, and
will host unrelated Projects. To avoid intentional or unintentional access between
projects, or to the shared Cluster Infrastructure, we use 
[Kubenetes Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
to isolate Projects from each other. Shared Cluster objects are deployed to multiple
namespaces, named like "kube-*" (e.g. kube-system, kube-dex, kube-dashboard, ...).

There is a distinct Active Directory Group for each Project, and one for Cluster
Administrators. The provisioning tools creates the nessersary Objects for the
default Configuration.

The isolation is not only implemented for the Kubernetes API. Pods from different
namespaces are not allowed to connect to each other by Pod or Service IP addresses.
We use a [Network Policy](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/),
for IP Isolation. This is like a Firewall between namespaces, or like using an own
IP Network for each Project.

---

## Private Registry for Docker-Images

To use private Docker Images, we need to deploy a Docker Registry (v2) within
the Cluster. We will use the Open-Source [Harbor](https://goharbor.io/) registry.
It implements Authenication one level of Isolation, like Kubernetes namespaces.
Harbor calles this [Projects](https://github.com/goharbor/harbor/blob/master/docs/1.10/administration/managing-users/_index.md).

The automatically provisioned default Configuration allows Images to be pulled
only from pods within a Kubernetes namespace only to the corresponding Harbor 
Project. There is an Harbor Project for shared Images, where every authenticated
user has pull access.

To push images to the Registry, you have to use an explicit Token, which will be
generated on provisioning, and needs to be configured to the Build-Pipeline.

---

## Centralized Logging

The Kubernetes Cluster supports an [Elastic Search](https://www.elastic.co/elasticsearch/service)
instance, with an [Kibana](https://www.elastic.co/kibana) which can be used 
to analyse logs to authenticated Users.

The default Configuration will capture the default output streams (stdout, stderr),
but you also by use Logging-Frameworks for deeper integration.

The Cluster Logging infrastructure will also be used to capture logs from
shared Cluster Components, to be used by the Cluster Administrators.

---

## Centralized Metrics and Monitoring

We use [Prometheus](https://prometheus.io/) to store metrics, and [Grafana](https://grafana.com/)
to visualize them in the Browser.

Metrics will be collected on different levels:

* Host: Physical Resources like: CPU, Memory or Disk Utilization
* Node: Status of Nodes within the Cluster like: Number of Pods, Resource-Usage by Namespaces, ...
* Application: Own Metrics, provided by the Application like: Number of current HTTP Requeestswerden.

## Unified Definition and Enforcement of Policies

To ensure overall Cluster-Health, it's not enough to implement project isolation.
We also need to enforce policies, like

* Maximum Replica count
* Maximum size of Netapp Volumes
* CPU and RAM Quotas by namespace
* Nameing Conventions
* Mandatory Labels

This is implemented by [Open Policy Agent](https://www.openpolicyagent.org/docs/v0.11.0/guides-kubernetes-admission-control/)

## Reproduceable and automated Cluster-Administration

k8s-setup implements the Cluster Administration processes in Software, like:

* Initialization of a new Cluster
* Upgrade of an existing Cluster
* Change Cluster Configuration
* Add additional Control Plane or Worker nodes
* Deploy additional features
* Create a new Project

It is developed using Agile Project Management, and produces Releases, which
have a semantic version number. To deploy new or updated Cluster-Features, you
have to update the k8s-setup tool, and re-run the provisioning.

This have the following advantages:

* Agile Implementation of new Features
* Reproduceable Clusters
* Efficient Cluster Management

## Local Development Mode

By using [Vagrant](https://www.vagrantup.com/), and [VirtualBox](https://www.virtualbox.org/),
anyone can provision a local k8s-setup Kubernetes Cluster, including all features
and components.

This not only allows to implement new features in isolation, but it also supports
testing szenarios like the failure of components or a node, or the upgrade of
components or the Kubernetes Version.

