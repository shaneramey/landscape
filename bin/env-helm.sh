#! /usr/bin/env bash
# set up Helm chart repos. FIXME: move to initialization method
helm repo add charts.downup.us http://charts.downup.us
helm repo remove local 2> /dev/null

helm repo update

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
