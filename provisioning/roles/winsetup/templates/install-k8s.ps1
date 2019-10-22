
$ErrorActionPreference = "Stop"

docker pull mcr.microsoft.com/windows/nanoserver:1809
docker tag mcr.microsoft.com/windows/nanoserver:1809 microsoft/nanoserver:latest
mkdir c:\k

# downloaded to c:\kubernetes.zip
Expand-Archive "c:\docker.zip" c:\

# root-extact dir is c:\kubernetes
# the binaries are in c:\kubernetes\nodes\bin\

copy c:\kubernetes\nodes\bin\*.exe c:\k\

# Copy Kubernetes certificate
#   TODO: check if this only applied to kubectl
#   TODO: check which cert (=serviceaccount) is acually needed, because we want
#   to avoid, that we put the admin.conf into a worker node.

# (Optional) Setup kubectl on Windows
# This will be skipped, because we don't plan to use kubectl directly on workers.



## TO CONFIGURE

# nodeSelector for linux by default
#https://docs.microsoft.com/en-us/virtualization/windowscontainers/kubernetes/creating-a-linux-master