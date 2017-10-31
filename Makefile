# Branch-aware management of clouds, clusters, and charts.
#
# Terraform clouds use files in the terraform/ dir of the landscape repo
# Helm chart secrets are deployed through process:
#  - landscape tool pulls environment variables out of Vault
#  - env vars are fed into landscaper
#  - landscaper deploys Helm charts and their secrets
#
# Intended pipeline.
# Running any of the below commands automatically runs all those above it.
# Alter with DEPLOY_LOCAL_REPOS, SKIP_CONVERGE_CLOUD, SKIP_CONVERGE_CLUSTER
# make repos
# make [DEPLOY_LOCAL_REPOS=true] [DRYRUN=true] cloud
# make [SKIP_CONVERGE_CLOUD=true] [DEPLOY_LOCAL_REPOS=true] [DRYRUN=true] cluster
# make [SKIP_CONVERGE_CLUSTER=true] [SKIP_CONVERGE_CLOUD=true] [DEPLOY_LOCAL_REPOS=true] [DRYRUN=true] charts
#
# A Jenkins pipeline might look like:
#  repos -> cloud -> cluster -> charts
#
# Acts on a single Landscape namespace at a time
# Smallest unit to CRUD is namespace
# Helm charts can be deployed independently
# landscaper will delete manually-installed helm charts in its namespaces
# Capable of deploying from either inside or outside target cluster
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
DEBUG := false

SHELL := /bin/bash

# Manages deployment of clouds, clusters, and charts.
CLOUD_NAME := minikube
CLUSTER_NAME := minikube
BRANCH_NAME := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)
DEPLOY_ONLY_NAMESPACES :=
# Whether to start local dev-vault and dev-chartmuseum containers and retrieve
DEPLOY_LOCAL_REPOS := false


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

.PHONY: repos cloud cluster charts

# Cloud deployment
ifneq (true,$(SKIP_CONVERGE_CLOUD))
cloud: repos
	$(eval CLOUD_NAME := $(shell landscape cluster show --cluster=$(CLUSTER_NAME) --cloud-id))
	@echo - Converging cloud for CLOUD_NAME=$(CLOUD_NAME)
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CLOUD_CMD)
else
	$(CONVERGE_CLOUD_CMD)
endif
else
cloud: repos
endif

# Cluster deployment
ifneq (true,$(SKIP_CONVERGE_CLUSTER))
cluster: repos cloud
	@echo - Converging cluster for CLUSTER_NAME=$(CLUSTER_NAME)
	@echo   - Setting CLOUD_NAME=$(CLOUD_NAME)
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CLUSTER_CMD)
else
	$(CONVERGE_CLUSTER_CMD)
endif
else:
cluster: repos
endif

# Charts deployment
charts: repos cluster cloud
	@echo - Converging Charts for CLUSTER_NAME=$(CLUSTER_NAME) CLOUD_NAME=$(CLOUD_NAME)
# deploy secrets from local repos
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CHARTS_CMD)
else
	$(CONVERGE_CHARTS_CMD)
endif

# cluster boostrapping/maintenance from workstation
# start local vault and chartmuseum containers
# to deploy from outside target cluster (e.g., a laptop)
repos:
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	@echo - Converging Local Repos
# use local docker-based vault + chartmuseum
# as opposed to using pre-existing Vault and Helm repo values
repos:
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
endif

