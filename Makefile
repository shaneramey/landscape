# Acts on a single Landscape namespace at a time (smallest unit to CRUD is namespace)
# Helm charts can be deployed independently of Landscaper using helm install / helm upgrade utils
#
# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`

GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

K8S_NAMESPACE := "__all_namespaces__"

export VAULT_TOKEN=$(shell docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $$3 }')

# FIXME: use https://github.com/shaneramey/vault-backup for backup/restore
WRITE_TO_VAULT_FROM_LASTPASS := false

LASTPASS_USERNAME := "set_LASTPASS_USERNAME_in_env_var"

# PROVISIONER can be minikube or kops. See also CLOUD_PROVIDER
PROVISIONER := minikube

DELETE_ALL_DATA := false

PURGE_NAMESPACE_ITSELF := false

.PHONY: bootstrap environment test deploy report purge # csr_approve

ifeq ($(WRITE_TO_VAULT_FROM_LASTPASS),true)
	lpass login $(LASTPASS_USERNAME)
	# prints `vault write` commands
	echo $(shell lpass show k8s-landscaper/$(GIT_BRANCH) --notes)
endif

all: environment test deploy verify report

bootstrap:
	./bin/env-install-prerequisites.sh
	./bin/init-vault-local.sh # create or start local dev-vault container
	./bin/init-${PROVISIONER}.sh # start cluster
	./bin/env-add-repos-helm.sh

environment:
	./bin/env-set-context-k8s.sh
	# FIXME: security hole. Create a more specific binding for Jenkins
	#kubectl create clusterrolebinding add-on-cluster-admin --clusterrole=cluster-admin --serviceaccount=kube-system:default

test:
	./bin/test.sh ${K8S_NAMESPACE}

verify:
	# need VPN connection if outside of Jenkins
	#sleep 7 # wait for kubedns to come up
	#./bin/verify.sh ${K8S_NAMESPACE}

deploy:
	./bin/deploy.sh ${GIT_BRANCH} ${K8S_NAMESPACE}

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
