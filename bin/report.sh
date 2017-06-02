#! /usr/bin/env bash

MINIKUBE_IP=`minikube ip`
NAMESPACE=$1
echo "Cluster service list"
echo
echo "cAdvisor: http://$MINIKUBE_IP:4194"
echo "k8s dashboard: http://kubernetes-dashboard.kube-system.svc.dev-seb.local"
echo
echo "to trust the minikube CA cert, run (MacOS):"
echo sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.minikube/ca.crt

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
