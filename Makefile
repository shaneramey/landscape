# Acts on a single Landscape namespace at a time (smallest unit to CRUD is namespace)
# Helm charts can be deployed independently of Landscaper using helm install / helm upgrade utils
#
# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#
# TODO: use https://github.com/shaneramey/vault-backup for backup/restore
#
#
# Usage:
#  make CLOUD_NAME=[ minikube | <GCE Project ID> ] deploy
SHELL := /bin/bash

# override these settings on command-line to override default behavior
DEBUG := false
BRANCH_NAME := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)
CLUSTER_NAME := minikube
# namespaces can be comma-separated
K8S_NAMESPACES = __all_namespaces__

# helm charts deployment
# also converges cluster (GKE/minikube) and cloud (GCE/minikube)
DEPLOY_CHARTS_CMD = landscape charts converge --git-branch=$(BRANCH_NAME) --cluster=$(CLUSTER_NAME) --converge-cluster --converge-cloud --converge-localmachine

ifeq ($(DEBUG),true)
	DEPLOY_CHARTS_CMD += --debug
endif

# Options for Helm Charts
ifneq ($(K8S_NAMESPACES),__all_namespaces__)
	DEPLOY_CHARTS_CMD += --namespaces=$(K8S_NAMESPACES)
endif

# Jenkinsfile stages, plus other targets
.PHONY: deploy init deploy-with-local-vault

deploy-with-local-vault: init
	source ./localvault.sh && $(DEPLOY_CHARTS_CMD)

deploy: init
	$(DEPLOY_CHARTS_CMD)

init:
# landscape prerequisites install
	helm init --client-only
	helm repo add charts.downup.us http://charts.downup.us
	helm repo update
