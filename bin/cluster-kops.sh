#! /usr/bin/env bash

CLOUD_PROVIDER=gke # or vsphere/aws
kops create cluster --admin-access=`curl http://ipecho.net/plain`/32 \
  --associate-public-ip=true --authorization=RBAC --cloud=${CLOUD_PROVIDER} \
  --cloud-labels=department=dev,owner=sramey --dns=public  --networking=calico \
  --node-count=1 --target=terraform --zones=us-west-2a --dns-zone=downup.us \
  --name=test7.downup.us