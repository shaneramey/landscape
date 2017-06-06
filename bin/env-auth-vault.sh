#! /usr/bin/env bash
GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`
CLUSTER_DOMAIN=${GIT_BRANCH}.local

# assume if VAULT_ADDR unset, we are running inside the cluster
# set the k8s-distributed ca.crt
if [ -z ${VAULT_ADDR+x} ]; then
    export VAULT_ADDR="https://http.vault.svc.${CLUSTER_DOMAIN}:8200"
    export VAULT_CACERT="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
fi
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
