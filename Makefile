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
#  make PROVISIONER=[ minikube | terraform ] [GCE_PROJECT=myproj-123456] deploy
SHELL := /bin/bash

CONTEXT_NAME := minikube
MINIKUBE_DRIVER := xhyve

# required for Terraform GCE deployments
GCE_PROJECT := ""

# override these settings on command-line for operations on a single namespace
K8S_NAMESPACE = __all_namespaces__
HELM_CHART_INSTALL = __all_charts__

DEBUG := false
# default command to deploy the cluster.
DEPLOY_CLUSTER_CMD = landscape cluster converge --context=$(CONTEXT_NAME)
# helm charts deployment
DEPLOY_CHARTS_CMD = landscape charts converge --context=$(CONTEXT_NAME)

ifeq ($(DEBUG),true)
	DEPLOY_CLUSTER_CMD += --debug
	DEPLOY_CHARTS_CMD += --debug
endif

# Options for Helm Charts
ifneq ($(K8S_NAMESPACE),__all_namespaces__)
	DEPLOY_CHARTS_CMD += --namespace=$(K8S_NAMESPACE)
endif
ifneq ($(HELM_CHART_INSTALL),__all_charts__)
	DEPLOY_CHARTS_CMD += --chart=$(HELM_CHART_INSTALL)
endif

# Jenkinsfile stages, plus other targets
.PHONY: init deploy

init:
	helm init --client-only
	helm repo add charts.downup.us http://charts.downup.us
	helm repo update

deploy: init
	$(DEPLOY_CLUSTER_CMD)
	helm repo update
	$(DEPLOY_CHARTS_CMD)
