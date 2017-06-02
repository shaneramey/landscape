#! /usr/bin/env bash
# when this command is run from inside a k8s cluster, it should use its own cluster vault
if [ -z ${VAULT_ADDR+x} ]; then
    export VAULT_ADDR="https://http.vault.svc.${CLUSTER_DOMAIN}:8200"
fi
unset VAULT_TOKEN # auth doesnt work unless this is unset
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
