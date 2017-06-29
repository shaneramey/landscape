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

# override for operations on a single namespace
K8S_NAMESPACE := "__all_namespaces__"

# `make purge` options
PURGE_NAMESPACE_ITSELF := false
DELETE_ALL_DATA := false

.PHONY: environment test deploy verify report purge # mostly Jenkinsfile stages

deploy: environment test
	./bin/deploy.sh ${GIT_BRANCH} ${K8S_NAMESPACE}

environment:
	./bin/env-install-prerequisites.sh
# populate local development secrets
ifeq ($(PROVISIONER),minikube)
	./bin/env-vault-local.sh
endif
	./bin/env-cluster-${PROVISIONER}.sh # start cluster
	./bin/env-set-context-k8s.sh
	./bin/env-add-repos-helm.sh

test: environment
	./bin/test.sh ${K8S_NAMESPACE}

verify:
	# need VPN connection if outside of Jenkins
	#sleep 7 # wait for kubedns to come up
	#./bin/verify.sh ${K8S_NAMESPACE}

report:
	./bin/report.sh ${K8S_NAMESPACE}

# helper targets not usually used in deployments, but useful for troubleshooting
#csr_approve:
#	./bin/csr_approve.sh

purge:
ifeq ($(K8S_NAMESPACE),kube-system)
	echo "purge not supported for kube-system namespace due to problems it creates with tiller api access"
endif

ifeq ($(DELETE_ALL_DATA),true)
	./bin/purge.sh ${K8S_NAMESPACE} $(PURGE_NAMESPACE_ITSELF)
else
	@echo "if you really want to purge, run \`make DELETE_ALL_DATA=true purge\`"
	@exit 1
endif
