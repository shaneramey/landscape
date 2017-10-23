#! /usr/bin/env bash
#
# Starts secrets in local vault container + overwrites its secrets from LastPass
# Starts ChartMuseum as local container

LASTPASS_USERNAME=$1
GOOGLE_STORAGE_BUCKET=$2
LASTPASS_SHARED_SECRETS_FOLDER=$3
CHARTS_BRANCH_FOR_SECRETS=$4

HASHICORP_VAULT_VERSION=0.8.3
CHARTMUSEUM_VERSION=v0.2.2

# check parameters
if [ -z "$LASTPASS_USERNAME" ]; then
	echo "LASTPASS_USERNAME required"
	exit 1
fi
if [ -z "$GOOGLE_STORAGE_BUCKET" ]; then
	echo "GOOGLE_STORAGE_BUCKET required"
	exit 1
fi
if [ -z "$LASTPASS_SHARED_SECRETS_FOLDER" ]; then
	echo "LASTPASS_SHARED_SECRETS_FOLDER required"
	exit 1
fi
if [ -z "$CHARTS_BRANCH_FOR_SECRETS" ]; then
	echo "CHARTS_BRANCH_FOR_SECRETS required"
	exit 1
fi

# start a local vault container, if it's not already running
DOCKER_VAULT_RUNNING=`docker inspect -f '{{.State.Running}}' dev-vault`
if [ "$DOCKER_VAULT_RUNNING" != "true" ]; then
	# check if vault container exists
	docker inspect dev-vault
	if [ $? != 0 ]; then
		# container doesnt exist. Create it
		docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault:${HASHICORP_VAULT_VERSION}
	else
		docker start dev-vault
	fi
fi

# start a local chartmuseum container, if it's not already running
DOCKER_CHARTMUSEUM_RUNNING=`docker inspect -f '{{.State.Running}}' dev-chartmuseum`
if [ "$DOCKER_CHARTMUSEUM_RUNNING" != "true" ]; then
	# check if chartmuseum container exists
	docker inspect dev-chartmuseum
	if [ $? != 0 ]; then
		# container doesnt exist. Create it
		docker run -p 8080:8080 -d --name=dev-chartmuseum \
			-e GOOGLE_APPLICATION_CREDENTIALS=/creds/application_default_credentials.json \
			-v $HOME/.config/gcloud:/creds chartmuseum/chartmuseum:${CHARTMUSEUM_VERSION} --port=8080 --debug \
			--storage=google --storage-google-bucket="${GOOGLE_STORAGE_BUCKET}"
	else
		docker start dev-chartmuseum
	fi
fi

# add chartmuseum chart repo
helm repo add chartmuseum http://127.0.0.1:8080

# overwrite existing secrets
VAULT_ADDR=http://127.0.0.1:8200 \
VAULT_TOKEN=$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $3 }')
landscape secrets overwrite --secrets-username="${LASTPASS_USERNAME}" --from-lastpass \
	--shared-secrets-folder="${LASTPASS_SHARED_SECRETS_FOLDER}/${CHARTS_BRANCH_FOR_SECRETS}"
