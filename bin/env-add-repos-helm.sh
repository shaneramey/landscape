#! /usr/bin/env bash
# set up Helm chart repos. FIXME: move to initialization method
helm init --client-only
helm repo add charts.downup.us http://charts.downup.us
helm repo remove local 2> /dev/null

helm repo update
