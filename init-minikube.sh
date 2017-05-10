#! /usr/bin/env bash

# Sets up minikube cluster
# - Starts minikube if it isn't running
# - mounts local ca.crt and ca.key (may be intermediate ca keypair)
# - enables default-storageclass ("standard" type)
# - adds local route to cluster
# - prints note about resolving DNS
# prereq: VirtualBox or other minikube host driver

## Note on ca.crt and ca.key
# to get started run
# openssl genrsa -out ~/external-pki/ca.key 2048
# openssl req -x509 -new -nodes -key ca.key -sha256 -days 1024 -out ca.crt
minikube_status=`minikube status --format {{.MinikubeStatus}}`
if [ "$minikube_status" == "Does Not Exist" ]; then
  if ! [ -f ~/external-pki/ca.crt ] || ! [ -f ~/external-pki/ca.key ]; then
    echo "~/external-pki/ca.crt and ~/external-pki/ca.key do not exist. Create them"
    exit 1
  fi
  echo "running 'minikube mount ~/external-pki' in background"
  minikube mount ~/external-pki:/mount-9p &
  minikube start --kubernetes-version=v1.6.0 \
    --extra-config=apiserver.Authorization.Mode=RBAC \
    --extra-config=apiserver.SecureServingOptions.CertDirectory=/mount-9p \
    --extra-config=apiserver.SecureServingOptions.PairName=ca \
    --extra-config=controller-manager.ClusterSigningCertFile=/mount-9p/ca.crt \
    --extra-config=controller-manager.ClusterSigningKeyFile=/mount-9p/ca.key \
    --cpus=4 \
    --disk-size=20g \
    --memory=4096

	# enable dynamic volume provisioning
	minikube addons enable default-storageclass

	# disable registry-creds add-on
	# https://github.com/kubernetes/minikube/blob/c23dfba5d25fc18b95c6896f3c98056cedce700f/deploy/addons/registry-creds/registry-creds-rc.yaml
	minikube addons disable registry-creds
elif [ "$minikube_status" == "Stopped" ]; then
	minikube start
fi

# cluster ip routing so you can hit kube-dns service 
echo "Need your password to add route to the service network"
sudo route delete 10.0.0.0/24
sudo route add 10.0.0.0/24 `minikube ip`

echo "NOTE: you may want to set /etc/resolv.conf to use nameserver 10.0.0.10"
echo "      try adding /etc/resolver/cluster.local w/ 10.0.0.10 as its nameserver (MacOS)"
echo "NOTE: you have to run 'minikube ssh' and kill -HUP the localkube process"
echo "NOTE: you may have to run \`kubectl create clusterrolebinding add-on-cluster-admin  --clusterrole=cluster-admin --serviceaccount=kube-system:default\`"
