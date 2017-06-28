#! /usr/bin/env bash

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

SCRIPT_DIR=var/terraform/

terraform plan \
	-var="branch_name=${GIT_BRANCH}" \
	-state=${GIT_BRANCH}.tfstate
	$SCRIPT_DIR

# FIXME: future: enable upload of our own CA signing cert/key
# to approve/issue CertificateSigningRequest objects
# if ! [ -f ~/external-pki/ca.pem ] || ! [ -f ~/external-pki/ca.key ]; then
#     echo
#     echo "~/external-pki/ca.{pem,key} keypair does not exist"
#     echo "Create them from an external CA and drop them here"
#     echo
#     exit 1
# fi