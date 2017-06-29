#! /usr/bin/env bash

# initializes a terraform cluster.
# if that's been done already, update the cluster
#
# Requires tfstate storage backend
# to create:
# export GOOGLE_APPLICATION_CREDENTIALS=downloaded-serviceaccount.json
#terraform init  -backend-config 'bucket=something-something-1234' \
#                -backend-config 'path=tfstate-dev-123456/master.tfstate' \
#                -backend-config 'project=dev-123456'
# - or possibly set (https://github.com/google/google-auth-library-ruby/issues/65#issuecomment-198532641) 
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_EMAIL=
# GOOGLE_ACCOUNT_TYPE=
# GOOGLE_PRIVATE_KEY= ?

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

# test syntax
pushd var/terraform
terraform validate && \
# prepare config
terraform plan -var="branch_name=${GIT_BRANCH}" && \
# apply if no error above
terraform apply -var="branch_name=${GIT_BRANCH}"
popd
