#! /usr/bin/env bash
# Set up local Vault backend

# check if vault already running
docker inspect dev-vault > /dev/null
if [ $? -ne 0 ]; then
	docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
fi
export VAULT_ADDR=http://127.0.0.1:8200
unset VAULT_TOKEN # auth doesnt work unless this is unset
sleep 3
vault auth `docker logs dev-vault 2>&1 | \
  grep '^Root\ Token' | awk -F ': ' '{ print $2 }' | tail -n 1`
