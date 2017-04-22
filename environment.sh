#! /usr/bin/env bash

# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm Charts

set -u

if [ -z ${VAULT_ADDR+x} ]; then
	echo "Configuration error. Set VAULT_ADDR (and other VAULT_ variables, if needed)"
	exit 2;
fi
vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | tail -n 1 | awk -F ': ' '{ print \$2 }'`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)

darwin=false; # MacOSX compatibility
case "`uname`" in
  Darwin*) export sed_cmd=`which gsed` ;;
  *) export sed_cmd=`which sed` ;;
esac

helm repo update
