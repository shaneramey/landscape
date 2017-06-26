#! /usr/bin/env bash

MINIKUBE_IP=`minikube ip`
NAMESPACE=$1

helm_list_cmd="helm list -q"
namespace_selector=""
if ! [ "$NAMESPACE" == "__all_namespaces__" ]; then
    namespace_selector=" --namespace=${NAMESPACE}"
fi
helm_list_cmd="$helm_list_cmd$namespace_selector"

echo "Helm Release Notes"
for release in `$helm_list_cmd`; do
    echo "-----" &&
    echo "Release: $release" &&
    helm status $release
done

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`
CLUSTER_DOMAIN=${GIT_BRANCH}.local
echo "#####"
echo "# CLUSTER SUMMARY"
echo "#"
echo "# Service list:"
echo "#"
echo "# cAdvisor: http://$MINIKUBE_IP:4194"
echo "# k8s dashboard: http://kubernetes-dashboard.kube-system.svc.${CLUSTER_DOMAIN}/"
echo "# jenkins: https://http.jenkins.svc.${CLUSTER_DOMAIN}/"
echo "# 389ds (LDAP): ldaps://ldap.dirsrv-389ds.svc.${CLUSTER_DOMAIN}:636"
echo "# vault: https://http.vault.svc.${CLUSTER_DOMAIN}:8200"
echo "# jenkins: https://http.jenkins.svc.${CLUSTER_DOMAIN}/"
echo "# prometheus: http://prom.prom.svc.${CLUSTER_DOMAIN}/"
echo "# alertmanager: http://alertmanager.prom.svc.${CLUSTER_DOMAIN}/"
echo "# openvpn: tcp://vpn.openvpn.svc.${CLUSTER_DOMAIN}:1194"
echo "# monocular: http://monocular-monocular-monocular-ui.monocular.svc.${CLUSTER_DOMAIN}/"
echo "# kubedns: dns://10.0.0.10:53"
echo "#"
echo "# note: check status of openvpn and vault 'helm status' output for client-side setup"
echo "#"
echo "# to trust the minikube CA cert, run (MacOS):"
echo "# sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.minikube/ca.crt"
echo "#"
echo "#####"
