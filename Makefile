# Branch-aware management of clouds, clusters, and charts.
#
# Terraform clouds use files in the terraform/ dir of the landscape repo
# Helm chart secrets are deployed through process:
#  - landscape tool pulls environment variables out of Vault
#  - env vars are fed into landscaper
#  - landscaper deploys Helm charts and their secrets
#
# Acts on a single Landscape namespace at a time
# Smallest unit to CRUD is namespace
# Helm charts can be deployed independently
# landscaper will delete manually-installed helm charts in its namespaces
# Capable of deploying from either inside or outside target cluster
#
# Intended pipeline:
#  reposetup -> cloud -> cluster -> charts
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


# Invoke with one of these arguments
# can use them for Jenkinsfile stages
.PHONY: reposetup cloud cluster charts

# Cloud deployment
ifneq (true,$(SKIP_CONVERGE_CLOUD))
cloud: reposetup
	echo Make Target: cloud
	$(CONVERGE_LOCAL_CLOUD_SETTINGS_CMD)
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CLOUD_CMD)
else
	$(CONVERGE_CLOUD_CMD)
endif
else
cloud: reposetup;
endif

# Cluster deployment
ifneq (true,$(SKIP_CONVERGE_CLUSTER))
cluster: reposetup cloud
	echo Make Target: cluster
	$(CONVERGE_LOCAL_CLUSTER_SETTINGS_CMD)
ifeq (true,$(DEPLOY_LOCAL_REPOS))
	VAULT_ADDR=http://127.0.0.1:8200 \
	VAULT_TOKEN=$$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }') \
	$(CONVERGE_CLUSTER_CMD)
else
	$(CONVERGE_CLUSTER_CMD)
endif
else:
cluster: reposetup
endif

# Charts deployment
charts: reposetup cluster cloud
	echo Make Target: charts
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
reposetup:
	echo Make Target: reposetup
ifeq (true,$(DEPLOY_LOCAL_REPOS))
# use local docker-based vault + chartmuseum
# as opposed to using pre-existing Vault and Helm repo values
reposetup:
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

