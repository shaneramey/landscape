#! /usr/bin/env bash
# Set up local Vault backend

# check if vault already running
RUNNING=$(docker inspect --format="{{.State.Running}}" dev-vault 2> /dev/null)

if [ $? -eq 1 ]; then
    docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
elif [ $RUNNING == "false" ]; then
	docker restart dev-vault
fi

sleep 3
