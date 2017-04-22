#! /usr/bin/env bash

# Requirements
#  - minikube
#  - gcr login access (needed for landscaper Makefile)
#  - Hashicorp vault container in local docker engine

# start minikube
minikube status
if [ $? -ne 0 ]; then
  minikube start --kubernetes-version=v1.6.0 \
    --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
    --cpus=4 \
    --disk-size=20g \
    --memory=4096
fi

# log in to your private registries
minikube addons enable registry-creds
# dynamic volume provisioning
minikube addons enable default-storageclass

# Set up local Vault backend
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
export VAULT_ADDR=https://127.0.0.1:8200
unset VAULT_TOKEN # auth doesnt work unless this is unset
vault auth `docker logs dev-vault 2>&1 | \
  grep '^Root\ Token' | awk -F ': ' '{ print $2 }' | tail -n 1`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)

# Authenticate to Google Container Registry

gcloud auth login
echo "Docker: logging into registry us.gcr.io"
echo "if Username prompt is 'oauthaccesstoken', just press Enter - and any password will work"
gcloud docker -- login us.gcr.io # any password should work if Username=oauth2accesstoken
docker login -e shane.ramey@gmail.com -u oauth2accesstoken -p "$(gcloud auth print-access-token)" https://us.gcr.io

# OPTIONAL: checkout which branch you want to deploy
#git checkout branch_i_want_to_deploy
## TIP: copy the produced `vault write` statements to a LastPass Secure Note

# TODO: First time only: Populate secrets
#make setsecrets # you'll be guided through adding/editing secrets
## TIP: copy the produced `vault write` statements to a LastPass Secure Note

# Set Kubernetes context
kubectl config use-context minikube # or cluster1, cluster2, etc.

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
make deploy

# minikube-only: cluster ip routing
echo "Need your password to add route to the service network"
sudo route delete 10.0.0.0/24
sudo route add 10.0.0.0/24 `minikube ip`
