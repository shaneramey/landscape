#! /usr/bin/env bash

kubectl get csr -o custom-columns=name:.metadata.name,status:.status | \
    grep 'map\[\]' | awk '{ print $1 }' | xargs kubectl certificate approve