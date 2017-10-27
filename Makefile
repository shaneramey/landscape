# Acts on a single Landscape namespace at a time (smallest unit to CRUD is namespace)
# Helm charts can be deployed independently of Landscaper using helm install / helm upgrade utils
# Capable of deploying from either inside or outside target cluster
#
# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#
# TODO: use https://github.com/shaneramey/vault-backup for backup/restore
#
#
# Usage:
#  make CLOUD_NAME=[ minikube | <GCE Project ID> ] [ deploy | bootstrap ]
SHELL := /bin/bash

# override these settings on command-line to override default behavior
DEBUG := false
BRANCH_NAME := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)
CLUSTER_NAME := minikube
# namespaces can be comma-separated. Default is to deploy all
DEPLOY_ONLY_NAMESPACES :=

# LastPass username for pulling centralized secrets
SHARED_SECRETS_USERNAME := 
SHARED_SECRETS_FOLDER := Shared-k8s/k8s-landscaper

# GCS backend for local Helm Chart repo (ChartMuseum)
GOOGLE_STORAGE_BUCKET := 
CHARTS_BRANCH_FOR_SECRETS := master
# helm charts deployment
# also converges cluster (GKE/minikube) and cloud (GCE/minikube)
DEPLOY_CHARTS_CMD = landscape charts converge --git-branch=$(BRANCH_NAME) --cluster=$(CLUSTER_NAME) --converge-cluster --converge-cloud --converge-localmachine

ifeq ($(DEBUG),true)
	DEPLOY_CHARTS_CMD += --debug
endif

# Options for Helm Charts
ifneq (,$(DEPLOY_ONLY_NAMESPACES))
	DEPLOY_CHARTS_CMD += --namespaces=$(DEPLOY_ONLY_NAMESPACES)
endif

# Jenkinsfile stages, plus other targets
.PHONY: deploy start_local_repos deploy_with_local_repos

# cluster boostrapping/maintenance from workstation
deploy_with_local_repos: init start_local_repos
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(DEPLOY_CHARTS_CMD)

# start local vault and chartmuseum containers (deploy from outside target cluster)
start_local_repos:
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	./start_local_repos.sh $(SHARED_SECRETS_USERNAME) $(GOOGLE_STORAGE_BUCKET) $(SHARED_SECRETS_FOLDER) $(CHARTS_BRANCH_FOR_SECRETS)

deploy: init
	$(DEPLOY_CHARTS_CMD)

init:
ifeq (,$(SHARED_SECRETS_USERNAME))
	$(error SHARED_SECRETS_USERNAME required to pull secrets from LastPass)
endif

ifeq (,$(GOOGLE_STORAGE_BUCKET))
	$(error GOOGLE_STORAGE_BUCKET required for Helm Charts repo via ChartMuseum)
endif
	# FUTURE? landscape prerequisites install
	helm init --client-only
	helm repo update
