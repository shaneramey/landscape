GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

.PHONY: bootstrap deploy

bootstrap:
	landscaper apply --dir kube-system/nfs-provisioner/ --namespace=kube-system

deploy:
	./deploy.sh

developer_min_resources:
	landscaper apply --dir kube-system/influxdb/ --namespace=kube-system
