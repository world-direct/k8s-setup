# Open ID Connect

Configuration Rational:

The API Server needs to be configured for trusting a specific CA. 
We will use the CA from /etc/kubernetes/pki/ca.crt. This CA (CN=kubernetes) is
part of the standard CA rotation (it is issued for 10 years at kubeadm init).

We should handle rotating this as part of a later TBD and TBI rotation.

To issue a server cert for dex, we use the internal signed from kube-controller-manager
https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/#set-up-a-signer

CA File Rotation: https://github.com/kubernetes/kubeadm/issues/1350



```sh
# test issue a server cert for dex

cat << EOF > /tmp/req.cnf
#!/bin/bash

mkdir -p ssl

cat << EOF > ssl/req.cnf
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = dex.example.com
EOF

openssl genrsa -out ssl/ca-key.pem 2048
openssl req -x509 -new -nodes -key ssl/ca-key.pem -days 10 -out ssl/ca.pem -subj "/CN=kube-ca"

openssl genrsa -out ssl/key.pem 2048
openssl req -new -key ssl/key.pem -out ssl/csr.pem -subj "/CN=kube-ca" -config ssl/req.cnf
openssl x509 -req -in ssl/csr.pem -CA ssl/ca.pem -CAkey ssl/ca-key.pem -CAcreateserial -out ssl/cert.pem -days 10 -extensions v3_req -extfile ssl/req.cnf
EOF

openssl genrsa -out ssl/ca-key.pem 2048
openssl req -x509 -new -nodes -key ssl/ca-key.pem -days 10 -out ssl/ca.pem -subj "/CN=kube-ca"

openssl genrsa -out ssl/key.pem 2048
openssl req -new -key ssl/key.pem -out ssl/csr.pem -subj "/CN=kube-ca" -config ssl/req.cnf
openssl x509 -req -in ssl/csr.pem -CA ssl/ca.pem -CAkey ssl/ca-key.pem -CAcreateserial -out ssl/cert.pem -days 10 -extensions v3_req -extfile ssl/req.cnf

```

# Tools

https://medium.com/@mrbobbytables/kubernetes-day-2-operations-authn-authz-with-oidc-and-a-little-help-from-keycloak-de4ea1bdbbe
https://www.keycloak.org/docs/latest/authorization_services/
https://itnext.io/protect-kubernetes-dashboard-with-openid-connect-104b9e75e39c
https://github.com/panva/node-oidc-provider/
https://github.com/int128/kubelogin
https://medium.com/@int128/kubectl-with-openid-connect-43120b451672