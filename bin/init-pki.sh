#! /usr/bin/env bash
#
# initializes a the following pki certs:
# - root CA ("ca.[crt, key]" - key gets put in LastPass; not stored in Vault)
# - intermediate CA used to sign everything ("intermediate.[crt, key]")
# - cluster intermediate CA cert ("cluster.[crt, key]")
#    - signed by cluster.crt:
#       etcd server ("etcd-server.[crt,key]")
#       etcd client ("etcd-client.[crt,key]")
#       pod client ("pod-client.key" CN=pod-client)
# - client signed by cluster.crt ("pod-client.key")
# - client certificate to talk to etcd ("etcd-client.[crt, key]")
# - k8s components tls arguments
#    - apiserver
#       - tls-cert-file: for https://kubernetes.default.svc/, etc.
#       - tls-private-key-file: for https://kubernetes.default.svc/, etc.
#       - ca-client-file: /var/run/secrets/kubernetes.io/ca.crt on pods
#       - ca cert chain to be placed in 
#       - etcd-certfile: client cert for k8s api
#       - etcd-keyfile: client key for k8s api
#       - etcd-cafile: ca cert to auth etcd server
#       - service-account-key-file=pod-client.key
#       - authorization-rbac-super-user=pod-client
#    - controller-manager
#       - root-ca-file ("cluster.crt")
#       - service-account-key-file=pod-client.key
#       - kubeconfig
#    - scheduler
#       - kubeconfig
#    - kube-proxy
#       - kubeconfig

WORK_DIR=ca-pki-init # .gitignored
CA_DIR=${WORK_DIR}/ca
INTERMEDIATE_DIR=${WORK_DIR}/intermediate
mkdir ${WORK_DIR} ${CA_DIR} ${INTERMEDIATE_DIR}

# create CA cert directories
for subdir in certs crt newcerts private; do
	mkdir ${CA_DIR}/${subdir}
	mkdir ${INTERMEDIATE_DIR}/${subdir}
done

# create intermediate cert directories
# Root CA cert
ROOT_CA_FILEPREFIX=ca
openssl genrsa -aes256 -out ${CA_DIR}/private/${ROOT_CA_FILEPREFIX}.key 4096 # enter passphrase, save to LastPass
chmod 400 ${CA_DIR}/private/${ROOT_CA_FILEPREFIX}.key
openssl req -config openssl-ca.cnf \
	-key ${CA_DIR}/private/${ROOT_CA_FILEPREFIX}.key \
	-new -x509 -days 7300 -sha256 -extensions v3_ca \
	-out ${CA_DIR}/certs/${ROOT_CA_FILEPREFIX}.crt

# Intermediate CA cert
INTERMEDIATE_CA_FILEPREFIX=intermediate
openssl genrsa -aes256 -out ${INTERMEDIATE_DIR}/private/${INTERMEDIATE_CA_FILEPREFIX}.key 4096
chmod 400 ${INTERMEDIATE_DIR}/private/${INTERMEDIATE_CA_FILEPREFIX}.key
openssl req -config openssl-int.cnf \
	-key ${CA_DIR}/private/${ROOT_CA_FILEPREFIX}.key \
	-new -x509 -days 7300 -sha256 -extensions v3_ca \
	-out ${INTERMEDIATE_DIR}/certs/${INTERMEDIATE_CA_FILEPREFIX}.crt

cat ${INTERMEDIATE_DIR}/certs/${INTERMEDIATE_CA_FILEPREFIX}.crt ${CA_DIR}/certs/${ROOT_CA_FILEPREFIX}.crt > ${WORK_DIR}/ca-chain.pem
