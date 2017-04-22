GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

.PHONY: environment test deploy

environment:
	./environment.sh

test:
	./test.sh

deploy:
	./deploy.sh

all: environment test deploy
