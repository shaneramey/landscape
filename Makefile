# Acts on a single Landscape namespace at a time (smallest unit to CRUD is namespace)
# Helm charts can be deployed independently of Landscaper using helm install / helm upgrade utils
# Capable of deploying from either inside or outside target cluster
#
# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#
# TODO: use https://github.com/shaneramey/vault-backup for backup/restore
#
# Intended pipeline:
#  localsetup -> cloud -> cluster -> charts
#
# Examples:
# - Bootstrapping from local machine
# make SHARED_SECRETS_USERNAME=username@lastpass.email \
#      GOOGLE_STORAGE_BUCKET=helm-charts-staging-123456 \
#      DEPLOY_ONLY_NAMESPACES=openvpn,389ds \
#      CLOUD_NAME=minikube \
#      DEPLOY_LOCAL_REPOS=true
#      (cloud|cluster|charts)
#
# - Running with existing Vault and ChartMuseum repos (set in env vars)
#   Deploy two Chart namespaces
# make DEPLOY_ONLY_NAMESPACES=openvpn,389ds \
#      CLUSTER_NAME=gke_staging-123456_us-west1-a_master \
#      (cloud|cluster|charts)

SHELL := /bin/bash

DEBUG := false
BRANCH_NAME := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)
CLUSTER_NAME := minikube
CLOUD_NAME := $(shell landscape cluster show \
				--cluster=$(CLUSTER_NAME) --cloud-id)
# Whether to start local dev-vault and dev-chartmuseum containers and retrieve
DEPLOY_LOCAL_REPOS := true


# LastPass team-shared secrets username (REQUIRED when DEPLOY_LOCAL_REPOS=true)
SHARED_SECRETS_USERNAME := 
SHARED_SECRETS_ITEM := $(BRANCH_NAME)
# GCS backend for local Helm Chart repo (REQUIRED when DEPLOY_LOCAL_REPOS=true)
GOOGLE_STORAGE_BUCKET := 


# Converge Cloud cluster (e.g., minikube, terraform(GKE), unmanaged)
CONVERGE_CLOUD_CMD = landscape cloud converge --cloud=$(CLOUD_NAME)

# Converge Kubernetes cluster
CONVERGE_CLUSTER_CMD = landscape cluster converge --cluster=$(CLUSTER_NAME)

# Converge Helm charts
# Optionally, deploy a sub-set (instead of the full-set), using CSV namespaces
CONVERGE_CHARTS_CMD = landscape charts converge --cluster=$(CLUSTER_NAME)
DEPLOY_ONLY_NAMESPACES :=
ifneq (,$(DEPLOY_ONLY_NAMESPACES))
	CONVERGE_CHARTS_CMD += --namespaces=$(DEPLOY_ONLY_NAMESPACES)
endif


# Simulate convergence but not apply
ifeq ($(DRYRUN),true)
	CONVERGE_CLOUD_CMD += --dry-run
	CONVERGE_CLUSTER_CMD += --dry-run
	CONVERGE_CHARTS_CMD += --dry-run
endif

# Debug output
ifeq ($(DEBUG),true)
	CONVERGE_CLOUD_CMD += --debug
	CONVERGE_CLUSTER_CMD += --debug
	CONVERGE_CHARTS_CMD += --debug
endif


# Jenkinsfile stages, plus other targets
.PHONY: cloud cluster charts localsetup start-local-repos

# Cloud deployment
ifeq (false,$(SKIP_CONVERGE_CLOUD))
cloud:
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CLOUD_CMD)
else
	$(CONVERGE_CLOUD_CMD)
endif
else
cloud: ;
endif

# Cluster deployment
ifeq (false,$(SKIP_CONVERGE_CLUSTER))
cluster: cloud
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CLUSTER_CMD)
else
	$(CONVERGE_CLUSTER_CMD)
endif
else:
cluster: ;
endif

charts: cluster cloud
# deploy secrets from local repos
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CHARTS_CMD)
else
	$(CONVERGE_CHARTS_CMD)
endif

# cluster boostrapping/maintenance from workstation
localsetup:
ifeq (true,$(DEPLOY_LOCAL_REPOS))
# use local docker-based vault + chartmuseum
# as opposed to using pre-existing Vault and Helm repo values
localsetup: start-local-repos
endif
	$(CONVERGE_LOCAL_CLOUD_SETTINGS_CMD)
	$(CONVERGE_LOCAL_CLUSTER_SETTINGS_CMD)
	helm init --client-only
	helm repo update

# start local vault and chartmuseum containers
# to deploy from outside target cluster
start-local-repos:
ifeq (,$(SHARED_SECRETS_USERNAME))
	$(error SHARED_SECRETS_USERNAME required to pull secrets from LastPass)
endif
ifeq (,$(GOOGLE_STORAGE_BUCKET))
	$(error GOOGLE_STORAGE_BUCKET required for Helm Charts repo via ChartMuseum)
endif
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	LASTPASS_USERNAME=$(SHARED_SECRETS_USERNAME) \
	CHARTS_STORAGE_BUCKET=$(GOOGLE_STORAGE_BUCKET) \
	SHARED_SECRETS_ITEM=$(BRANCH_NAME) \
	./start_local_repos.sh
