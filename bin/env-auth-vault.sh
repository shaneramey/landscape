#! /usr/bin/env bash

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`
CLUSTER_DOMAIN="${GIT_BRANCH}.local"

# assume we've already authed
# FIXME: this only works with a manual `vault auth` on the pod right now
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
# only use local vault if cluster-vault isn't available
# test if inside k8s cluster
INSIDE_K8S_CACERT='/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
VAULT_CACERT=~/.minikube/ca.crt 
if [ -f "$INSIDE_K8S_CACERT" ]; then
	VAULT_CACERT=$INSIDE_K8S_CACERT
fi

# test connection
export VAULT_ADDR="https://http.vault.svc.${CLUSTER_DOMAIN}:8200"
vault list /secret > /dev/null

# if connection fails, fall back to local Vault
if [ $? -ne 0 ]; then
	export VAULT_ADDR="http://127.0.0.1:8200"
fi

