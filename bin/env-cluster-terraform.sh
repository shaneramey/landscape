#! /usr/bin/env bash

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

# test syntax
terraform validate var/terraform && \
# prepare config
terraform plan -var="branch_name=${GIT_BRANCH}" var/terraform && \
# apply if no error above
terraform apply -var="branch_name=${GIT_BRANCH}" var/terraform
