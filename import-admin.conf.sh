#!/bin/sh
set -ex

file=$2
wd=$(mktemp -d)

if [ ! -e "$file" ]; then
    echo "$file not found"
    exit 1
fi

extract() {
    cat $file | grep "$1: " | awk '{print $2}' > /$wd/$1
    cat /$wd/$1
}

extract "certificate-authority-data"
extract "server"
extract "client-certificate-data"
extract "client-key-data"

kubectl config set-cluster $1 \
    --server=$(cat $wd/server) \
    --certificate-authority=$wd/certificate-authority-data \
    --embed-certs=true

kubectl config set-context $1 \
    --cluster=$1 \
    --namespace=default \
    --user=$1-admin

kubectl config set-credentials $1-admin \
    --client-certificate=$wd/client-certificate-data \
    --client-key=$wd/client-key-data \
    --embed-certs=true

rm -rf $wd