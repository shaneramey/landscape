GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

K8S_NAMESPACE := "__all_namespaces__"

WRITE_TO_VAULT_FROM_LASTPASS := false

LASTPASS_USERNAME := "shane.ramey@gmail.com"

PROVISIONER := minikube

PURGE_ALL := no

.PHONY: environment test deploy csr_approve purge

ifeq ($(WRITE_TO_VAULT_FROM_LASTPASS),true)
	lpass login $(LASTPASS_USERNAME)
	# prints `vault write` commands
	echo $(shell lpass show k8s-landscaper/$(GIT_BRANCH) --notes)
endif

all: init_cluster environment test deploy verify csr_approve

init_cluster:
	./init-vault-local.sh # create or start local dev-vault container
	./init-${PROVISIONER}.sh # start cluster

environment:
	./environment.sh ${K8S_NAMESPACE}

test:
	./test.sh ${K8S_NAMESPACE}

verify:
	sleep 10 # wait for kubedns to come up
	./verify.sh ${K8S_NAMESPACE}

deploy: init_cluster environment test
	./deploy.sh ${K8S_NAMESPACE}

csr_approve:
	kubectl get csr -o "jsonpath={.items[*].metadata.name}" | xargs kubectl certificate approve

purge:
	if [ "$(PURGE_ALL)" == "yes" ]; then \
		helm list -q | xargs helm delete --purge ; \
		for resource_type in rs ns; do \
			kubectl --namespace=kube-system get $$resource_type -o 'jsonpath={.items[*].metadata.name}' | xargs kubectl --namespace=kube-system delete $$resource_type ; \
		done ; \
	fi

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#make deploy

