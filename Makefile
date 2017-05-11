GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

K8S_NAMESPACE := "__all_namespaces__"

WRITE_TO_VAULT_FROM_LASTPASS := false

LASTPASS_USERNAME := "shane.ramey@gmail.com"

PROVISIONER := minikube

PURGE_ALL="no"

.PHONY: init_cluster lastpass_to_vault environment test deploy csr_approve purge

ifeq ($(WRITE_TO_VAULT_FROM_LASTPASS),true)
	lpass login $(LASTPASS_USERNAME)
	# prints `vault write` commands
	echo $(shell lpass show k8s-landscaper/$(GIT_BRANCH) --notes)
endif

init_cluster:
	./init-vault-local.sh # create or start local dev-vault container
	./init-${PROVISIONER}.sh # start cluster
	helm init # install Helm into cluster
	@echo waiting 5s for tiller pod to be Ready
	sleep 5
	kubectl get pod  --namespace=kube-system -l app=helm -l name=tiller

environment:
	./environment.sh ${K8S_NAMESPACE}

test:
	./test.sh ${K8S_NAMESPACE}

deploy: init_cluster environment test
	./deploy.sh ${K8S_NAMESPACE}

csr_approve:
	kubectl get csr -o "jsonpath={.items[*].metadata.name}" | xargs kubectl certificate approve

purge:
	if [ "$$PURGE_ALL" == "yes" ]; then \
		helm list -q | xargs helm delete --purge \
	fi

all: init_cluster lastpass_to_vault environment test deploy csr_approve

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#make deploy

