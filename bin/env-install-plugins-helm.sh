#! /usr/bin/env bash

# install plugins
if ! [ -d ~/.helm/plugins/helm-local-bump ]; then
    helm plugin install https://github.com/shaneramey/helm-local-bump
    pip install -r  ~/.helm/plugins/helm-local-bump/requirements.txt
fi

if ! [ -d ~/.helm/plugins/helm-template ]; then
    helm plugin install https://github.com/technosophos/helm-template \
    --version=2.4.1+2
    helm template -h # verify installed properly
fi
