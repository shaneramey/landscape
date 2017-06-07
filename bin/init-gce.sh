#! /usr/bin/env bash

PROJECT=

REGION=

CLUSTER_DOMAIN=

terraform apply \
	-var="region=${REGION}" \
	-var="project=${PROJECT}" \
	-var="clusterDomain=${GIT_BRANCH}.local"
