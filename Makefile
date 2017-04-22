GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

K8S_NAMESPACE="somefakenamespace"

.PHONY: environment test deploy

environment:
	./environment.sh ${K8S_NAMESPACE}

test:
	./test.sh ${K8S_NAMESPACE}

deploy:
	./deploy.sh ${K8S_NAMESPACE}

all: environment test deploy
