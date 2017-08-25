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

CLOUD_NAME := minikube
CONTEXT_NAME := minikube
MINIKUBE_DRIVER := xhyve

# override these settings on command-line for operations on a single namespace
K8S_CLUSTER = __all_clusters__
K8S_NAMESPACE = __all_namespaces__
HELM_CHART_INSTALL = __all_charts__

DEBUG := false
# default command to deploy the cloud.
DEPLOY_CLOUD_CMD = landscape cloud converge --cloud=$(CLOUD_NAME)
# default command to deploy the cluster.
DEPLOY_CLUSTER_CMD = landscape cluster converge --cloud=$(CLOUD_NAME)
# helm charts deployment
DEPLOY_CHARTS_CMD = landscape charts converge --cloud=$(CLOUD_NAME) --context=$(CONTEXT_NAME)

ifeq ($(DEBUG),true)
	DEPLOY_CLOUD_CMD += --debug
	DEPLOY_CLUSTER_CMD += --debug
	DEPLOY_CHARTS_CMD += --debug
endif

# Which Kubernetes clusters to converge
ifneq ($(K8S_CLUSTER),__all_clusters__)
	DEPLOY_CLUSTER_CMD += --cluster=$(K8S_CLUSTER)
endif

# Options for Helm Charts
ifneq ($(K8S_NAMESPACE),__all_namespaces__)
	DEPLOY_CHARTS_CMD += --namespace=$(K8S_NAMESPACE)
endif
ifneq ($(HELM_CHART_INSTALL),__all_charts__)
	DEPLOY_CHARTS_CMD += --chart=$(HELM_CHART_INSTALL)
endif

# Jenkinsfile stages, plus other targets
.PHONY: deploy init 

deploy: init
	$(DEPLOY_CLOUD_CMD)
	$(DEPLOY_CLUSTER_CMD)
	helm repo update
	$(DEPLOY_CHARTS_CMD)

init:
	landscape tools install
	helm init --client-only
	helm repo add charts.downup.us http://charts.downup.us
	helm repo update

