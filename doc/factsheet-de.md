---
theme : "moon"
transition: "slide"
highlightTheme: "monokai"
logoImg: "https://github.com/kubernetes/kubernetes/raw/master/logo/logo.png"
slideNumber: false
title: "World-Direct k8s-setup"
---

## **k8s-setup**

*This document describes the k8s-setup project, to automatically install and manage a kubernetes cluster*

guenter.prossliner@world-direct.at

02.03.2020

---

# Introduction

Dieses Dokument beschreibt die Zielsetzung des k8s-setup Projektes, und beschreibt
deren bereits durchgeführte, oder bereits geplante Umsetzung.

Um Kubernetes in der Organisation einzuführen, wurde ein internes Projekt 
gestartet, welches folgende Ziele implementieren muss:

---

## Hybrider Kubernetes Cluster

Es ist geplant, Kubernetes für den Betrieb von folgenden Arten von Anwendungen 
zu verwenden:

* Eigene Windows Anwendungen: Das sind vor allem Anwendungen, welche für das 
.NET Framework geschrieben wurden. Ausserdem beinhalten diese oft auch Windows-Services,
sowie administrative Tools.

* Eigene .NET Core Anwendungen: Neuere Projekte werden standardmäsig für .NET Core
entwickelt. Diese können sowohl unter Windows als auch unter Linux gehostet werden.

* Fremdanwendungen: Dies sind Anwendungen, für welche die Images nicht selbst erstellt
werden. Ein Beispiel dafür ist eine Elastic-Search Instanz, oder eine Wordpress
Seite mit zugehöriger Datenbank. Viele dieser Images können nur in Linux Containern
gestartet werden.

Aus diesen Anwendungstypen ergibt sich die Notwendigkeit, sowohl Windows- als auch 
Linux-Container im Kubernetes Cluster zu hosten. In Kubernetes wird das als "hybrider 
Cluster" bezeichnet.

Wir wollen die verschiedenen Platformen nicht zu nebeneinander betreiben können.
Sie sollten sich auch die selben Features implementieren. Ausserdem muss das Management
der einzelnen Platformen gleich sein.

[^1]des

---

## Anmeldung über Active Directory

Kubernetes bringt selbst gar keine Benutzerverwaltung mit, sondern bietet diverse
Möglichkeiten zu Integration einer externen Benutzerverwaltung. Wir verwenden das
LDAP Modul von DEX[^1], welches über Open ID Connect in Kubernetes integriert ist.

Diese Konfiguration macht es möglich, dass Benutzer sich über ihren Domain-Account
am Kubernetes-Frontend anmelden können. Ausgehend vom Windows-Account ist es ist auch möglich, 
einen Standard Kubernetes Kontext zu konfigurieren, welches für API basierten Zugriff,
welche auch für das "kubectl" Kommandozeilen-Program notwendig ist. Diese Konfiguration
wird über ein Tool unterstützt.

Um zu vermeiden, Benutzer anhand ihres Benutzernamens zu authorieren, werden die
relevanten Active-Directory Gruppen zur Administration von Rollenmitgliedschaften
verwendet.

---

## Zugriffskontrolle und Isolation von Projekten

Ein einzelner Kubernetes-Cluster wird von mehreren Organisationseinheiten und
Projekten gemeinsam genutzt. Um absichtliche oder versehendliche Zugriffe auf andere
Projekte - oder die gemeinsame Cluster-Infrastruktur - zu unterbinden, wird eine 
Isolations-Ebene implementiert. Das erfolgt auf der Basis von Kubernetes "Namespaces".

Über die Mitgliedschaft in Active-Directory Gruppen, werden Benutzern Berechtigungen
für einzelne Projekte gegeben. Es gibt auch eine Gruppe für das Zuweisen von Cluster-Admins.

Die Isolation von Projekten sollte nicht nur für die Kubernetes-API gelten. Die Pods
(also Container) sollten sich auch netzwerktechnisch nicht erreichen können. Das
lässt sich mit einem eigenen IP-Subnetz für jedes Projekt vergleichen.

---

## Private Registry für Docker-Images

Um private Docker Images verwenden zu können, muss eine Docker Registry (v2) im
Kubernetes Cluster vorhanden sein. Wir werden dazu die "Harbor" Registry verwenden.
Diese implementiert ebenfalls eine Zugriffskontrolle und Isolation. In diesem 
Kontext wird aber von "Project", und nicht von "Namespace" gesprochen.

Die automatisierte Standardkonfiguration eines neuen Projektes ist so, dass Pods
einen Kubernetes Namespaces die entsprechenden Images im Harbor Projekt lesen (pull) 
können.

Für das Schreiben (push) ist ein explizites Token erforderlich, welche automatisch
generiert, und in der Build-Pipeline konfiguriert wird.

---

## Einheitliches Logging

Der Kubernetes Cluster stellt ein einheitliches Logging für Anwendungen zur Verfügung.
Im einfachesten Fall werden die Ausgaben (stdout, stderr) der Container verwenden.
Im speziellen Fall können Adapter von entsprechenden Logging-Frameworks integriert werden.

Der Benutzer kann dann, nach der Authentifizierung, über ein Kibana Frontend auf
die Logdaten der Anwendungen zugreifen.

Die Logging-Infrastruktur wird auch für clusterinterne Komponenten konfiguriert, 
und steht den Cluster-Admins zur Verfügung.

## Einheitliches Monitoring

Es werden Metriken auf folgenden Ebenen gesammelt und gespeichert:

* Host: Auslastung von Ressourcen wie CPU, Memory oder Disk
* Node: Status von Nodes im Kubernetes Cluster, Anzahl Pods, Ressourcen nach Projekt und Pod
* Anwendung: Eigene Metriken, welcher von Applikationen als Prometheus Endpunkt bereitgestellt werden.

## Einheitliche Verwaltung von Policies

Neben der Isolation von Projekten, muss auch gewährleistet werden, dass die 
Konfiguration der Projekte bestimmten Regeln genügt, wie z.B.

* Maximale Anzahl von Replicas
* Maximale Grösse von Netapp Volumes
* CPU und RAM Quotas nach Namespace
* Konventionen zur Benennung von Entitäten

Das wird über die Integration des "Open Policy Frameworks" implementiert.

## Reproduzierbare und automatisierte Cluster-Administration

Kubernetes Cluster werden wie Software entwickelt und verteilt. Diese haben eine
sematische Versionsnummer. Über die automatisierte Konfiguration des Clusters werden
folgende Ziele erreicht:

* Agile Weiterentwicklung des Clusters
* Reproduzierbare Umgebungen
* Effizienz in der Cluster-Verwaltung

## Entwicklungs-Modus

Ein über k8s-setup erstellter Kubernetes-Cluster kann nicht nur auf 
existierenden Hosts aufgesetzt werden.

Über Vagrant und VirtualBox kann ein solcher Cluster (k8stest.local), inklusive
aller Komponenten auch lokal erstellt und aktualisiert werden.

Das ermöglicht zum einen die lokale Weiterentwicklung der Konfiguration bzw. Automatisierung,
erlaubt es zum anderen aber auch Anwendungsentwicklern das Testen von Szenarien 
wie dem Ausfall einzelnen Hosts oder Komponenten, oder die Aktualisierung von
einzelnen Cluster-Komponenten oder Kubernetes selbst.

