# Acts on a single Landscape namespace at a time (smallest unit to CRUD is namespace)
# Helm charts can be deployed independently of Landscaper using helm install / helm upgrade utils
GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

K8S_NAMESPACE := "__all_namespaces__"

WRITE_TO_VAULT_FROM_LASTPASS := false

LASTPASS_USERNAME := "shane.ramey@gmail.com"

PROVISIONER := minikube

DELETE_ALL_DATA := false

.PHONY: environment test deploy csr_approve purge

ifeq ($(WRITE_TO_VAULT_FROM_LASTPASS),true)
	lpass login $(LASTPASS_USERNAME)
	# prints `vault write` commands
	echo $(shell lpass show k8s-landscaper/$(GIT_BRANCH) --notes)
endif

all: init_cluster environment test deploy verify csr_approve

init_cluster:
	./bin/init-vault-local.sh # create or start local dev-vault container
	./bin/init-${PROVISIONER}.sh # start cluster

environment:
	./bin/environment.sh ${K8S_NAMESPACE}

test:
	./bin/test.sh ${K8S_NAMESPACE}

verify:
	# need VPN connection if outside of Jenkins
	#sleep 7 # wait for kubedns to come up
	#./verify.sh ${K8S_NAMESPACE}

deploy:
	./bin/deploy.sh ${K8S_NAMESPACE}

csr_approve:
	kubectl get csr -o "jsonpath={.items[*].metadata.name}" | xargs kubectl certificate approve

purge:
ifeq ($(DELETE_ALL_DATA),true)
	./bin/purge.sh ${K8S_NAMESPACE}
	helm init
else
	@echo "if you really want to purge, run \`make DELETE_ALL_DATA=true purge\`"
	@exit 1
endif

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#make deploy

