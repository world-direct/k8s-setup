# -*- mode: ruby -*-
# vi: set ft=ruby :


## VM CONFIGURATION
#
# For the nodes to communicate, we use the following network configuration
#   10.0.0.0/24
#
# We have the following dynamic ranges:
#   10.0.0.10-19: Control Plane Nodes
#   10.0.0.20-29: Linux Worker Nodes
#   10.0.0.30-39: Windows Worker Nodes
#   10.0.0.40-49: None-Cluster Nodes (like Test-Clients or AD Server)
#
# Special Addresses:
#   
#   Reserved for Gateway
#   10.0.0.1
#
#   VIP (keepalived) for Control-Plane apiserver (k8s_apiserver_port=443)
#   10.0.0.2 (K8S_API_SERVER_VIP)

# Install vagrant plugins if required
def ensure_plugin(name)
    unless Vagrant.has_plugin?(name)
        system("vagrant plugin install #{name}")
    end
end

# https://github.com/gosuri/vagrant-env
# Allows us to put configuration values in .env
ensure_plugin("vagrant-env")

# https://github.com/oscar-stack/vagrant-hosts
# Allows us to use host-resolution internaly, without DNS
ensure_plugin("vagrant-hosts")


Vagrant.configure(2) do |config|

    # enable the vagrant-env
    config.env.enable

    # virtualbox configuration
    config.vm.provider "virtualbox" do |vb|
        vb.memory = ENV['BOX_MEMORY']
        vb.cpus = ENV['BOX_CPUS']
        vb.linked_clone = true
    end

    config.vm.provision :hosts do |p|
        # p.sync_hosts = true
        p.autoconfigure = true
        p.add_host ENV['K8S_API_SERVER_VIP'], ["#{ENV['K8S_APISERVER_HOSTNAME']}.#{ENV['K8S_CLUSTER_DNSNAME']}"]
    end

    #   10.0.0.10-19: Control Plane Nodes
    (1..ENV['LNX_NR_CLPS'].to_i).each do |nr|
        config.vm.define "lnxclp#{nr}" do |cpl|
            cpl.vm.box=ENV['LNX_BOX_NAME']
            cpl.vm.hostname = "lnxclp#{nr}"
            cpl.vm.network "private_network", ip:"10.0.0.#{9+nr}"
        end
    end

    # 10.0.0.20-29: Linux Worker Nodes
    (1..ENV['LNX_NR_WORKERS'].to_i).each do |nr|
        config.vm.define "lnxwrk#{nr}" do |worker|
            worker.vm.box=ENV['LNX_BOX_NAME']
            worker.vm.hostname = "lnxwrk#{nr}"
            worker.vm.network "private_network", ip:"10.0.0.#{19+nr}"
        end
    end

    # 10.0.0.30-39: Windows Worker Nodes
    (1..ENV['WIN_NR_WORKERS'].to_i).each do |nr|
        config.vm.define "winwrk#{nr}" do |worker|
            worker.vm.box=ENV['WIN_BOX_NAME']
            worker.vm.hostname = "winwrk#{nr}"
            worker.vm.network "private_network", ip:"10.0.0.#{29+nr}"
        end
    end

    # 10.0.0.40-49: None-Cluster Nodes (like Test-Clients or AD Server)
    # define a single client box
    #   1. for test
    #   2. to execute the ansible setup in paralell
    config.vm.define "client" do |client|
        client.vm.box=ENV['LNX_BOX_NAME']
        client.vm.hostname = "lnxclient"
        client.vm.network "private_network", ip:"10.0.0.40"

        client.vm.provision :ansible do |ansible|

            # because limit="all", the playbook is executed on all machines in parallel
            # even if it is triggered by "client", which is the last in the Vagrantfile
            # This ensures, that
            #   1. ansible provisioner is called only once
            #   2. ansible provisioner is called after others
            ansible.limit = "all"

            # groups are not configured by a hostname pattern, because this generates a warning:
            # > Vagrant has detected a host range pattern in the `groups` option.
            # > Vagrant doesn't fully check the validity of these parameters!

            ansible.groups = {

                # only the setup node needs to be configured statically
                "lnxclp-setup" => ["lnxclp1"],
                "lnxclp" => [],
                "lnxwrk" => [],
                "winwrk" => [],
                "winwrk:vars" => {
                    "ansible_winrm_scheme" => "http",
                    "ansible_become" => false
                }
            }

            (1..ENV['LNX_NR_CLPS'].to_i).each do |nr|
                ansible.groups["lnxclp"] << "lnxclp#{nr}"
            end

            (1..ENV['LNX_NR_WORKERS'].to_i).each do |nr|
                ansible.groups["lnxwrk"] << "lnxwrk#{nr}"
            end

            (1..ENV['WIN_NR_WORKERS'].to_i).each do |nr|
                ansible.groups["winwrk"] << "winwrk#{nr}"
            end

            # pass the needed vars from the .env
            ansible.extra_vars = {
                k8s_api_server_vip: ENV['K8S_API_SERVER_VIP'],
                k8s_cluster_dnsname: ENV['K8S_CLUSTER_DNSNAME'],
                k8s_apiserver_hostname: ENV['K8S_APISERVER_HOSTNAME'],
                k8s_enable_proxy: true,
                host_primary_interface_name: 'eth1'
            }

            ansible.become = true
            ansible.playbook = "provisioning/hostplaybook.yml"
            ansible.compatibility_mode = "2.0"

            # ansible.verbose = "vvvv"
        end
    end

end
