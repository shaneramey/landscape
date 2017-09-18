#! /usr/bin/env bash

DOCKER_VAULT_EXISTS=`docker inspect -f '{{.State.Running}}' dev-vault`
if [ $? == 0 ]; then
	docker start dev-vault
else
	docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault:0.8.2
fi
sleep 5
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $3 }')

