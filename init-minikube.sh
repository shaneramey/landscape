#! /usr/bin/env bash

# Sets up minikube cluster
# - Starts minikube if it isn't running
# - mounts local ca.pem and ca.key for tls key signing (may be intermediate ca keypair)
# - enables default-storageclass ("standard" type)
# - adds local route to cluster
# - adds dns resolver for cluster
# prereq: VirtualBox or other minikube host driver

## Note on ca.pem and ca.key
# to get started run
# openssl genrsa -out ~/external-pki/ca.key 2048
# openssl req -x509 -new -nodes -key ca.key -sha256 -days 1024 -out ca.pem

# TODO
#--extra-config=apiserver.SecureServingOptions.CertDirectory=/mount-9p \
#--extra-config=apiserver.SecureServingOptions.PairName=ca \

minikube_status=`minikube status --format {{.MinikubeStatus}}`

if [ "$minikube_status" == "Does Not Exist" ]; then
  if ! [ -f ~/external-pki/ca.pem ] || ! [ -f ~/external-pki/ca.key ]; then
    echo "~/external-pki/ca.pem and ~/external-pki/ca.key do not exist. Create them"
    exit 1
  fi
  minikube start --kubernetes-version=v1.6.0 \
    --extra-config=apiserver.Authorization.Mode=RBAC \
    --cpus=4 \
    --disk-size=20g \
    --memory=4096
  echo "mounting /etc/kubernetes/ca inside minikube"
  minikube mount ~/external-pki:/etc/kubernetes/ca -v=8 &

  # restart minikube to use mounted files
  minikube stop
  minikube start
  # enable dynamic volume provisioning
  minikube addons disable kube-dns # DNS deployed via Landscaper/Helm Chart
  minikube addons enable default-storageclass
  minikube addons enable ingress
  minikube addons disable registry-creds # FIXME: https://github.com/kubernetes/minikube/blob/c23dfba5d25fc18b95c6896f3c98056cedce700f/deploy/addons/registry-creds/registry-creds-rc.yaml needs to be deployed first

elif [ "$minikube_status" == "Stopped" ]; then
	minikube start
fi

# cluster ip routing so you can hit kube-dns service 
GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`
netstat -rn | grep `minikube ip` | grep 10/24 > /dev/null
ROUTE_NEEDED=$?
if ! [ -f /etc/resolver/${GIT_BRANCH}.local ] || [ $ROUTE_NEEDED != 0 ]; then
  echo Enter your local machine password to:
  echo " - add route to the service network inside k8s"
  echo " - set /etc/resolver/${GIT_BRANCH}.local to use 10.0.0.10"
  sudo route delete 10.0.0.0/24
  sudo route add 10.0.0.0/24 `minikube ip`
  sudo sh -c "echo nameserver 10.0.0.10 > /etc/resolver/${GIT_BRANCH}.local"

  echo "NOTE: you may have to run \`kubectl create clusterrolebinding add-on-cluster-admin  --clusterrole=cluster-admin --serviceaccount=kube-system:default\`"
fi

# install Helm tiller pod into cluster
kubectl get pod  --namespace=kube-system -l app=helm -l name=tiller > /dev/null
if [ $? -ne 0 ]; then
  helm init
  echo waiting 5s for tiller pod to be Ready
  sleep 5
fi
