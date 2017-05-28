#! /usr/bin/env bash

MINIKUBE_IP=`minikube ip`
echo "cAdvisor: http://$MINIKUBE_IP:4194"

echo "to trust the minikube CA cert, run (MacOS):"
echo sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.minikube/ca.crt

echo "Helm Release Notes"
for release in `helm list -q`; do
    echo "-----" &&
    echo "Release: $release" &&
    helm status $release
done
