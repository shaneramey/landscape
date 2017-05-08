#! /usr/bin/env bash
set -u
# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm Charts
CLUSTER_DOMAIN=`grep search /etc/resolv.conf | awk '{ print $NF }'`

# Set Kubernetes context
kubectl config use-context minikube # or cluster1, cluster2, etc.

# Set kubeconfig if running in Jenkins inside of Kubernetes
if ! [ -z ${JENKINS_SECRET+x} ] && ! [ -z ${KUBERNETES_PORT} ]; then
	kubectl config set preferences.colors true
	kubectl config set-cluster ${CLUSTER_DOMAIN} --server=https://kubernetes.default.svc.${CLUSTER_DOMAIN} --api-version=v1
	kubectl config set-credentials clusterrole --token=`cat /var/run/kubernetes.io/secrets/token`
	kubectl config set-context ${CLUSTER_DOMAIN} --cluster=${CLUSTER_DOMAIN} --user=clusterrole --namespace=default
	kubectl config use-context ${CLUSTER_DOMAIN}
fi

# Install 
if [ -z ${VAULT_ADDR+x} ]; then
	export VAULT_ADDR=http://http.vault.svc.${CLUSTER_DOMAIN}
fi
unset VAULT_TOKEN # auth doesnt work unless this is unset
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
