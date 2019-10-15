# -*- mode: ruby -*-
# vi: set ft=ruby :


## VM CONFIGURATION
#
# For the nodes to communicate, we use the following network configuration
#   10.0.0.0/24
#
# The first master has: 10.0.0.2
# Next masters:         10.0.0.3, 10.0.0.4
# Master virtual IP:    10.0.0.10
# Linux-Workers:              10.0.0.11-10.0.0.20
# Windows-Workers:              10.0.0.21-10.0.0.29


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

def config_vm(node)
    node.vm.provision :hosts do |p|
        # p.sync_hosts = true
        p.autoconfigure = true
        p.add_host '10.0.0.1', ['master.k8s.vm']
    end
end

# currently this is only possible on a sole master
def config_master(master)
    # Bind kubernetes admin port so we can administrate from host
    master.vm.network "forwarded_port", guest: 6443, host: 6443, hostip: "10.0.0.10"

    # Bind kubernetes default proxy port
    master.vm.network "forwarded_port", guest: 8001, host: 8001, hostip: "10.0.0.10"
end

Vagrant.configure(2) do |config|

    # enable the vagrant-env
    config.env.enable

    # virtualbox configuration
    config.vm.provider "virtualbox" do |vb|
        vb.memory = ENV['BOX_MEMORY']
        vb.cpus = ENV['BOX_CPUS']
        vb.linked_clone = true
    end

    # first controlplane
    config.vm.define "lnxclp1" do |master|
        master.vm.box=ENV['LNX_BOX_NAME']
        master.vm.hostname = "lnxclp1.k8s.vm"
        master.vm.network "private_network", ip:"10.0.0.2"

        config_vm(master)
        config_master(master)
    end

    # linux workers
    (1..ENV['LNX_NR_WORKERS'].to_i).each do |nr|
        config.vm.define "lnxwrk#{nr}" do |worker|
            worker.vm.box=ENV['LNX_BOX_NAME']
            worker.vm.hostname = "lnxwrk#{nr}.k8s.vm"
            worker.vm.network "private_network", ip:"10.0.0.#{10+nr}"
    
            config_vm(worker)
        end
    end

    # windows workers
    (1..ENV['WIN_NR_WORKERS'].to_i).each do |nr|
        config.vm.define "winwrk#{nr}" do |worker|
            worker.vm.box=ENV['WIN_BOX_NAME']
            worker.vm.hostname = "lnxwrk#{nr}"
            worker.vm.network "private_network", ip:"10.0.0.#{20+nr}"
    
            config_vm(worker)
        end
    end

    # workers are not added by a hostname pattern, because this generates a warning:
    # > Vagrant has detected a host range pattern in the `groups` option.
    # > Vagrant doesn't fully check the validity of these parameters!
    config.vm.provision "ansible" do |ansible|

        # TODO: dynamically create for each windows worker
        ansible.host_vars = { 
           "winwrk1" => {
               "ansible_winrm_scheme" => "http",
               "ansible_become" => false
            }
        }

        ansible.groups = {
          "lnxclp" => ["lnxclp1"],
          "lnxwrk" => ["lnxwrk1", "lnxwrk2"],
          "winwrk" => ["winwrk1"]
        }

        (1..ENV['NR_LNX_WORKERS'].to_i).each do |nr|
            ansible.groups["lnxwrk"] << "lnxwrk#{nr}"
        end

        (1..ENV['NR_WIN_WORKERS'].to_i).each do |nr|
            ansible.groups["winwrk"] << "winwrk#{nr}"
        end

        ansible.become = true
        ansible.playbook = "provisioning/playbook.yml"
        ansible.compatibility_mode = "2.0"

        # ansible.verbose = "vvv"
    end
end
