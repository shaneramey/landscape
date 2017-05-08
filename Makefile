GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

K8S_NAMESPACE="somefakenamespace"

PROVISIONER="minikube"

.PHONY: environment test deploy

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

all: environment test deploy

# Deploy environment
#  deploys to current branch to context in `kubectl config current-context`
make deploy
