#! /usr/bin/env bash

LASTPASS_SHARED_SECRETS_FOLDER=$1
CHARTS_BRANCH_FOR_SECRETS=$2

if [ -z "$LASTPASS_SHARED_SECRETS_FOLDER" ]; then
	LASTPASS_SHARED_SECRETS_FOLDER="Shared-k8s/k8s-landscaper"
fi

if [ -z "$CHARTS_BRANCH_FOR_SECRETS" ]; then
	CHARTS_BRANCH_FOR_SECRETS="master"
fi

DOCKER_VAULT_EXISTS=`docker inspect -f '{{.State.Running}}' dev-vault`
if [ $? == 0 ]; then
	docker start dev-vault
else
	docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault:0.8.2
fi
echo "Sleeping to allow dev-vault to start"
sleep 5
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $3 }')
landscape secrets overwrite --from-lastpass --shared-secrets-folder="$LASTPASS_SHARED_SECRETS_FOLDER/$CHARTS_BRANCH_FOR_SECRETS"
