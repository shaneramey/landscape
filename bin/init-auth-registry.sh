#! /usr/bin/env bash
# Authenticate to Google Container Registry

gcloud auth login
echo "Docker: logging into registry us.gcr.io"
echo "if Username prompt is 'oauthaccesstoken', just press Enter - and any password will work"
gcloud docker -- login us.gcr.io # any password should work if Username=oauth2accesstoken
docker login -e shane.ramey@gmail.com -u oauth2accesstoken -p "$(gcloud auth print-access-token)" https://us.gcr.io

# OPTIONAL: checkout which branch you want to deploy
#git checkout branch_i_want_to_deploy
## TIP: copy the produced `vault write` statements to a LastPass Secure Note

# TODO: First time only: Populate secrets
#make setsecrets # you'll be guided through adding/editing secrets
## TIP: copy the produced `vault write` statements to a LastPass Secure Note
