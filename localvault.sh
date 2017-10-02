#! /usr/bin/env bash

LASTPASS_USERNAME=$1
LASTPASS_SHARED_SECRETS_FOLDER=$2
CHARTS_BRANCH_FOR_SECRETS=$3

if [ -z "$LASTPASS_USERNAME" ]; then
	echo "LASTPASS_USERNAME required"
	exit 1
fi
if [ -z "$LASTPASS_SHARED_SECRETS_FOLDER" ]; then
	LASTPASS_SHARED_SECRETS_FOLDER="Shared-k8s/k8s-landscaper"
fi

if [ -z "$CHARTS_BRANCH_FOR_SECRETS" ]; then
	CHARTS_BRANCH_FOR_SECRETS="master"
fi

# start a local dev-vault, if it's not already running
DOCKER_VAULT_RUNNING=`docker inspect -f '{{.State.Running}}' dev-vault`
if [ "$DOCKER_VAULT_RUNNING" != "true" ]; then
	# check if vault exists
	docker inspect dev-vault
	if [ $? != 0 ]; then
		# container doesnt exist. Create it
		docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault:0.8.2
	else
		docker start dev-vault
	fi
fi
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $3 }')
landscape secrets overwrite --secrets-username="$LASTPASS_USERNAME" --from-lastpass --shared-secrets-folder="$LASTPASS_SHARED_SECRETS_FOLDER/$CHARTS_BRANCH_FOR_SECRETS"
