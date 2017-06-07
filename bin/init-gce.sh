#! /usr/bin/env bash

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