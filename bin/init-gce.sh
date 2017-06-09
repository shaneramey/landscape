#! /usr/bin/env bash

# FIXME: future: enable upload of our own CA signing cert/key
# to approve/issue CertificateSigningRequest objects
# if ! [ -f ~/external-pki/ca.pem ] || ! [ -f ~/external-pki/ca.key ]; then
#     echo
#     echo "~/external-pki/ca.{pem,key} keypair does not exist"
#     echo "Create them from an external CA and drop them here"
#     echo
#     exit 1
# fi

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

PROJECT=develop

REGION=us-central1

CLUSTER_DOMAIN="cluster.local"

SCRIPT_DIR=var/terraform/

NETWORK1_IPV4_CIDR="10.128.0.0/14"
NETWORK2_IPV4_CIDR="10.132.0.0/14"

echo $SCRIPT_DIR

terraform plan \
	-var="region=${REGION}" \
	-var="project=${PROJECT}" \
	-var="branch_name=${GIT_BRANCH}" \
	-var="network1_ipv4_cidr=${NETWORK1_IPV4_CIDR}" \
	-var="network2_ipv4_cidr=${NETWORK2_IPV4_CIDR}" \
	$SCRIPT_DIR