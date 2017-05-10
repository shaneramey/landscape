GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

K8S_NAMESPACE="somefakenamespace"

PROVISIONER="minikube"

PURGE_ALL="no"

.PHONY: environment test deploy purge

init:
	./init-vault-local.sh # create or start local dev-vault container
	./init-${PROVISIONER}.sh # start cluster
	helm init # install Helm into cluster

environment:
	./environment.sh ${K8S_NAMESPACE}

test:
	./test.sh ${K8S_NAMESPACE}

deploy: #init environment test
	./deploy.sh ${K8S_NAMESPACE}

csr_approve:
	kubectl get csr -o "jsonpath={.items[*].metadata.name}" | xargs kubectl certificate approve
purge:
	if [ "$$PURGE_ALL" == "yes" ]; then \
		helm list -q | xargs helm delete --purge \
	fi

all: environment test deploy csr_approve

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
#make deploy

# FIXME:
# future parameters
# Network parameters
# - apiserver
#   - service-cluster-ip-range
# - kube-proxy
#   - masquarade-all
# - kubelet
#   - cluster-dns
#   - cluster-domain
#   - network-plugin
#   - resolv-conf

# Other parameters
# - kubernetes-apiserver
#   - allow-privileged
# - kubelet
#   - allow-privileged

# Container parameters
# - apiserver
#   - allow-provileged

# Other considerations
# - kubernetes federation
