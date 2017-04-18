#! /usr/bin/env bash

# Requirements
#  - minikube
#  - gcr login access
#  - Hashicorp vault container in local docker engine

# start minikube
minikube start --kubernetes-version=v1.6.0 \
  --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
  --cpus 4 \
  --disk-size 20g \
  --memory 4096

# log in to your private registries
minikube addons enable registry-creds

# Set up local Vault backend
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
export VAULT_ADDR=http://127.0.0.1:8200
unset VAULT_TOKEN # auth doesnt work unless this is unset
vault auth `docker logs dev-vault 2>&1 | \
  grep '^Root\ Token' | awk -F ': ' '{ print $2 }' | tail -n 1`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)

# Authenticate to Google Container Registry
gcloud auth login
gcloud docker -- login us.gcr.io
docker login -e shane.ramey@gmail.com -u oauth2accesstoken -p "$(gcloud auth print-access-token)" https://us.gcr.io

# Add Helm Chart Repo
helm repo add charts.downup.us http://charts.downup.us

# Install helm local_bump plugin
helm plugin install https://github.com/shaneramey/helm-local-bump

# OPTIONAL: checkout which branch you want to deploy
#git checkout branch_i_want_to_deploy
## TIP: copy the produced `vault write` statements to a LastPass Secure Note

# TODO: First time only: Populate secrets
#make setsecrets # you'll be guided through adding/editing secrets
## TIP: copy the produced `vault write` statements to a LastPass Secure Note

# Set Kubernetes context
kubectl config use-context minikube # or cluster1, cluster2, etc.

# Install Helm Tiller into cluster
helm init && sleep 10

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
make deploy

# minikube-only: cluster ip routing
sudo route add 10.0.0.0/24 `minikube ip`
