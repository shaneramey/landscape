#! /usr/bin/env bash
#
# Starts secrets in local vault container + overwrites its secrets from LastPass
# Starts ChartMuseum as local container
#
# Environment Variables:
#  - LASTPASS_USERNAME: Username for centralized secrets
#  - CHARTS_STORAGE_BUCKET: ChartMuseum GCS storage bucket
#  - LASTPASS_SHARED_SECRETS_FOLDER: LastPass folder for centralized secrets
#  - SHARED_SECRETS_ITEM: entry in LastPass folder to read for secrets

HASHICORP_VAULT_VERSION=0.8.3
CHARTMUSEUM_VERSION=v0.2.2

# check parameters
if [ -z "$LASTPASS_USERNAME" ]; then
	echo "LASTPASS_USERNAME required"
	exit 1
fi
if [ -z "$CHARTS_STORAGE_BUCKET" ]; then
	echo "CHARTS_STORAGE_BUCKET required"
	exit 1
fi
if [ -z "$SHARED_SECRETS_ITEM" ]; then
	echo "SHARED_SECRETS_ITEM required"
	exit 1
fi

LASTPASS_SHARED_SECRETS_FOLDER="Shared-k8s/k8s-landscaper"

# start a local vault container, if it's not already running
DOCKER_VAULT_RUNNING=`docker inspect -f '{{.State.Running}}' dev-vault`
if [ "$DOCKER_VAULT_RUNNING" != "true" ]; then
	# check if vault container exists
	docker inspect dev-vault > /dev/null
	if [ $? != 0 ]; then
		echo "dev-vault container doesnt exist. Creating it"
		docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault:${HASHICORP_VAULT_VERSION}
	else
		echo "dev-vault container exists but not started. Starting it"
		docker start dev-vault
		sleep 3
	fi
else
	echo "dev-vault container already running."
fi

# start a local chartmuseum container, if it's not already running
DOCKER_CHARTMUSEUM_RUNNING=`docker inspect -f '{{.State.Running}}' dev-chartmuseum`
if [ "$DOCKER_CHARTMUSEUM_RUNNING" != "true" ]; then
	# check if chartmuseum container exists
	docker inspect dev-chartmuseum > /dev/null
	if [ $? != 0 ]; then
		echo "dev-chartmuseum container doesnt exist. Creating it"
		docker run -p 8080:8080 -d --name=dev-chartmuseum \
			-e GOOGLE_APPLICATION_CREDENTIALS=/creds/application_default_credentials.json \
			-v $HOME/.config/gcloud:/creds chartmuseum/chartmuseum:${CHARTMUSEUM_VERSION} --port=8080 --debug \
			--storage=google --storage-google-bucket="${CHARTS_STORAGE_BUCKET}"
	else
		echo "dev-chartmuseum container exists but not started. Starting it"
		docker start dev-chartmuseum
		sleep 3
	fi
else
	echo "dev-chartmuseum container already running."
fi

# add chartmuseum chart repo
helm repo add chartmuseum http://127.0.0.1:8080

# pull secrets from LastPass to local vault container
VAULT_ADDR=http://127.0.0.1:8200 \
VAULT_TOKEN=$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $3 }')
landscape secrets overwrite --secrets-username="${SHARED_SECRETS_USERNAME}" --from-lastpass \
	--shared-secrets-folder="${LASTPASS_SHARED_SECRETS_FOLDER}/${SHARED_SECRETS_ITEM}"
