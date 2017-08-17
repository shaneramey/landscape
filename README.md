# landscape: portable Kubernetes datacenter configuration
deploy k8s clusters + apps to:
- minikube
- GKE
- Any other Kubernetes cluster to which you have credentials

Apps are deployed via Helm Charts, with secrets kept in Vault until deployment

## Getting started
1. install landscape wrapper tool included in this repo
```
python3 -m venv ~/venv && \
source ~/venv/bin/activate && \
pip install git+ssh://git@github.com/oreillymedia/landscape.git

```

2. clone this repo

3. run `make`

## Prerequisites
Should be installed automatically, if missing
- helm
- vault
- minikube
- landscaper
- google cloud tools

## Credentials

Terraform Credentials needed (envvars):

 GOOGLE_CREDENTIALS (json): Authenticate with GCS for Terraform state storage.
 	- automatically pulled from Hashicorp Vault /secrets/terraform/$(GCE_PROJECT_ID)

 VAULT_ADDR: URL of the Vault server
 	- must be set in environment or specified on command line

 VAULT_CACERT: TLS CA cert to verify Vault server cert against
 	- must be set in environment or specified on command line

 VAULT_TOKEN: Authentication token to Vault
 	- added via vault auth -method=ldap username=admin

populating a base Vault secret-set in the future will be done with `landscape environment --read-lastpass`

Until then, `vault write` statements are shared in the LastPass folder "Shared-k8s\landscaper\master"

## Vault paths

/secret/terraform/$(GCE_PROJECT_ID)/auth['credentials'] = GCE credentials JSON

/secret/k8s_contexts/$(CONTEXT_NAME): kubeconfig secrets (used by Jenkins)

/secret/landscape/$(GIT_BRANCH): Helm secrets, deployed via Landscaper

## Troubleshooting

- Error messages
```
Failed to load backend:
Error configuring the backend "gcs": Failed to configure remote backend "gcs": google: could not find default credentials.
```

This means you don't have GOOGLE_CREDENTIALS set. Run `gcloud auth activate-service-account` to remedy.


- minikube clock out of sync
```
minikube ssh -- docker run -i --rm --privileged --pid=host debian nsenter -t 1 -m -u -n -i date -u $(date -u +%m%d%H%M%Y)
```
