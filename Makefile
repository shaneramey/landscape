# Acts on a single Landscape namespace at a time (smallest unit to CRUD is namespace)
# Helm charts can be deployed independently of Landscaper using helm install / helm upgrade utils
#
# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#
# TODO: use https://github.com/shaneramey/vault-backup for backup/restore
#
#
# Usage:
#  make PROVISIONER=[ minikube | terraform ] [GCE_PROJECT=myproj-123456] deploy

PROVISIONER := minikube

GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

DNS_DOMAIN := cluster.local

GCE_PROJECT_ID := please_pass_gce_project_id
# override for operations on a single namespace
K8S_NAMESPACE := "__all_namespaces__"

# default command to deploy the cluster.
# intention is to append to this command, based on the provisioner
DEPLOY_CMD := landscape deploy --provisioner=$(PROVISIONER) --cluster-domain=$(DNS_DOMAIN)
# `make purge` flags
PURGE_NAMESPACE_ITSELF := false
DELETE_ALL_DATA := false

# Jenkinsfile stages, plus other targets
.PHONY: environment test deploy verify report purge csr_approve

deploy: environment test
ifeq ($(PROVISIONER),terraform)
	${DEPLOY_CMD} --gce-project-id=$(GCE_PROJECT_ID)
else
	${DEPLOY_CMD}
endif

environment:
	# landscape set-context --provisioner=minikube
	# landscape helm-add-repos
	./bin/env-set-context-k8s.sh
	./bin/env-add-repos-helm.sh

test: environment
	landscape test

verify:
	# disable until functional/useful
	#sleep 7 # wait for kubedns to come up
	# ./bin/verify.sh ${K8S_NAMESPACE}

report:
	landscape report ${K8S_NAMESPACE}

purge:
ifeq ($(K8S_NAMESPACE),kube-system)
	echo "purge not supported for kube-system namespace due to problems it creates with tiller api access"
endif

ifeq ($(DELETE_ALL_DATA),true)
	landscape purge ${K8S_NAMESPACE} $(PURGE_NAMESPACE_ITSELF)
else
	@echo "if you really want to purge, run \`make DELETE_ALL_DATA=true purge\`"
	@exit 1
endif
