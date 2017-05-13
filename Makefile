# Acts on a single Landscape namespace at a time (smallest unit to CRUD is namespace)
# Helm charts can be deployed independently of Landscaper using helm install / helm upgrade utils
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
	# need VPN connection if outside of Jenkins
	#sleep 7 # wait for kubedns to come up
	#./verify.sh ${K8S_NAMESPACE}

deploy:
	./deploy.sh ${K8S_NAMESPACE}

csr_approve:
	kubectl get csr -o "jsonpath={.items[*].metadata.name}" | xargs kubectl certificate approve

purge:
	./purge.sh ${K8S_NAMESPACE}

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#make deploy

