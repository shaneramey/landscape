#! /usr/bin/env bash
set -u
# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm Charts
CLUSTER_DOMAIN=`grep search /etc/resolv.conf | awk '{ print $NF }'`

# Install 
if [ -z ${VAULT_ADDR+x} ]; then
	export VAULT_ADDR=http://http.vault.svc.${CLUSTER_DOMAIN}
fi
unset VAULT_TOKEN # auth doesnt work unless this is unset
vault auth 00deadbeef
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)

darwin=false; # MacOSX compatibility
case "`uname`" in
  Darwin*) export sed_cmd=`which gsed` ;;
  *) export sed_cmd=`which sed` ;;
esac

helm repo add charts.downup.us http://charts.downup.us
helm repo update
helm plugin install https://github.com/shaneramey/helm-local-bump

sleep 10 && helm init && sleep 10