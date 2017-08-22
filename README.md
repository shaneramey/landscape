# landscape: portable Kubernetes configuration

## Features
Deploy k8s clusters + apps (Helm Charts) to:
- minikube
- GKE
- Any other Kubernetes cluster to which you have credentials

It does this in a portable way, by abstracting cluster provisioning, and centralizing secrets in Vault

Apps are deployed via Helm Charts, with secrets kept in Vault until deployment

## Getting started
1. install landscape wrapper tool included in this repo
```
python3 -m venv ~/venv && \
source ~/venv/bin/activate && \
pip install git+ssh://git@github.com/oreillymedia/landscape.git

```

2. clone this repo

3. start a local dev-vault server and update your environment variables, to point to it:
```
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=$(docker logs dev-vault 2>&1 | grep 'Root Token' | tail -n 1 | awk '{ print $3 }')
```

4. Put the secrets from LastPass into your local Vault
Copy and paste the output from this command:
```
lpass show Shared-k8s/k8s-landscaper/master --notes
```

5. run `make`

## Once cluster is up
- Verify that the cluster is running by issuing the command:
```
kubectl version --context=minikube
```

- generate OpenVPN profile to connect to the cluster
```
helm status openvpn-openvpn | grep -v '^.*#' | sed -e '1,/generate_openvpn_profile:/d'
```

Copy and paste the output into a shell to generate a Viscosity profile setup

Navigate to the directory you ran the command from, and double-click the .ovpn file to import it

## Prerequisites
Should be installed automatically, if missing
- kubectl
- vault
- helm
- vault
- minikube
- landscaper

You may also want to download the [Google Cloud SDK](https://cloud.google.com/sdk/)

## Credentials

populating a base Vault secret-set in the future will be done with `landscape environment --read-lastpass`

Until then, `vault write` statements are shared in the LastPass folder "Shared-k8s\landscaper\master"

## Vault paths

/secret/terraform/$(GCE_PROJECT_ID)/auth['credentials'] = GCE credentials JSON

/secret/k8s_contexts/$(CONTEXT_NAME): kubeconfig secrets (used by Jenkins)

/secret/landscape/$(GIT_BRANCH): Helm secrets, deployed via Landscaper

## Secrets set up

### minikube secrets

### terraform secrets (for GCE/GKE)
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
