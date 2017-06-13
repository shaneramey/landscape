#! /usr/bin/env bash
set -u
# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm Charts
# contexts are named after cluster domains (which are in-turn dependent
# on branch names) (.e.g, "master.local")

CLUSTER_DOMAIN=`grep search /etc/resolv.conf | awk '{ print $NF }'`

# Inside Kubernetes:
# Create kubeconfig if we detect script in Jenkins inside of Kubernetes
if ! [ -z ${JENKINS_SECRET+x} ] && ! [ -z ${KUBERNETES_PORT} ]; then
    kubectl config set preferences.colors true

    kubectl config set-cluster ${CLUSTER_DOMAIN} \
    --server=https://kubernetes.default.svc.${CLUSTER_DOMAIN} --api-version=v1
    
    kubectl config set-credentials clusterrole \
    --token=`cat /var/run/secrets/kubernetes.io/serviceaccount/token`
    
    kubectl config set-context ${CLUSTER_DOMAIN} \
    --cluster=${CLUSTER_DOMAIN} --user=clusterrole --namespace=default \
    --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    
    kubectl config use-context ${CLUSTER_DOMAIN}
    echo begin
    kubectl config view
    echo end
fi
