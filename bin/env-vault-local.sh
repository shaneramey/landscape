#! /usr/bin/env bash
# Set up local Vault backend

# pull in secrets from LastPass shared folder

# prints `vault write` commands
function lastpass_fetch_secrets {
    LASTPASS_FOLDER="Shared-k8s/k8s-landscaper"

    if ! [ -z "$LASTPASS_USERNAME" ]; then
        echo "ERROR: Please set LASTPASS_USERNAME environment variable"
    fi
    lpass login ${LASTPASS_USERNAME}
    lpass show $(LASTPASS_FOLDER)/$(GIT_BRANCH) --notes
}



# check if vault already running
RUNNING=$(docker inspect --format="{{.State.Running}}" dev-vault 2> /dev/null)

if [ $? -eq 1 ]; then
    docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
elif [ "$RUNNING" == "false" ]; then
    docker restart dev-vault
fi

sleep 3 # wait for vault to warm up
export VAULT_TOKEN=`docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $3 }'`
export VAULT_ADDR=http://127.0.0.1:8200

# test login - even though setting VAULT_TOKEN should be sufficient
vault auth ${VAULT_TOKEN}
