# Landscape: Place kubernetes clusters, charts, and secrets into clouds

## Quick Start:
run `make` to launch a minikube cluster. See Makefile for other options.

## Features
Deploy k8s clusters + apps (Helm Charts) to:
- minikube
- GKE
- Any other Kubernetes cluster to which you have credentials

It does this in a portable way, by abstracting cluster provisioning, and centralizing secrets in Vault

Apps are deployed via Helm Charts, with secrets kept in Vault until deployment

## Example Usage
 - List all clouds stored in Vault
```
landscape cloud list
```

 - List all clusters
```
landscape cluster list
```

 - Converge cloud
```
landscape cloud converge
```

 - Converge cloud then cluster
```
landscape cluster converge --converge-cloud
```

 - Verify cloud, clusters, and charts can be pulled from Vault
```
for cloud_name in `landscape cloud list`; do
        echo saw cloud ${cloud_name}
done

for cluster_name in `landscape cluster list`; do
        echo saw cluster ${cluster_name}
        landscape charts list --cluster=${cluster_name}
done
```

## minikube HTTP Proxy
Applies to minikube clusters

If set, HTTP_PROXY and HTTPS_PROXY will be used for docker image caching
Run squid on your local machine for fastest results
```brew install squid && brew services start squid```

Set up your local ~/.bash_profile:
```
cat << EOF > ~/.bash_profile
DEFAULT_INTERFACE=`netstat -rn | grep default | head -n 1 | awk '{ print $NF }'`
DEFAULT_IP=`ifconfig $DEFAULT_INTERFACE | grep inet | awk '{ print $2 }'`
export https_proxy=http://${DEFAULT_IP}:3128
export HTTPS_PROXY="$https_proxy"
export http_proxy="$https_proxy"
export HTTP_PROXY="$https_proxy"
export no_proxy=http.chartmuseum.svc.cluster.local,storage.googleapis.com
EOF
```

open a new shell to use these environment variables

# Create a virtualenv and activate it
```
python3.6 -m venv ~/venv
source ~/venv/bin/activate

# Install landscape tool
pip install --upgrade .

# install prerequisites
landscape setup install-prerequisites

## Bootstrap local setup
Deploys to local docker containers:
 - hashicorp vault
 - chartmuseum Helm chart server

make SHARED_SECRETS_USERNAME=<lastpass_username> GOOGLE_STORAGE_BUCKET=<chart_gcs_bucket> local deploy

# Connect to a VPN inside your cluster
helm status openvpn-openvpn # copy the create_viscosity_profile section
                            # and run it in your shell
open minikube-master.ovpn # Import Viscosity profile into MacOS

# Connect to minikube-master. admin credentials are pulled from LastPass
# via the above `make` command.

# Open https://http.jenkins.svc.cluster.local in your browser
```

## Getting Started (cloud-mode via Terraform)
 - Add Jenkinsfile to a Jenkins job
 - Open https://http.jenkins.svc.cluster.local in your browser

## Cluster-specific provisioning

### minikube

- Import minikube ca.crt into your MacOS keychain
```
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.minikube/ca.crt
```

### GKE
1. list clusters
```
landscape cluster list
```

2. deploy cluster (GCE/GKE terraform template + helm charts)
```
make CLUSTER_NAME=gke_staging-123456_us-west1-a_master
```

or
```
landscape charts converge --git-branch=${BRANCH_NAME} --cluster=${CLUSTER_NAME} --converge-cluster --converge-cloud
```

## Once cluster is up
- Verify that the cluster is running by issuing the command:
```
kubectl version --context=${CONTEXT_NAME}
```

- generate OpenVPN profile to connect to the cluster
```
helm status openvpn-openvpn | grep -v '^.*#' | sed -e '1,/generate_openvpn_profile:/d'
```

- Copy and paste the output into a shell to generate a Viscosity profile setup

- open the VPN profile  (it has a .ovpn extension)

- Username and password are what is in Vault /openvpn/ sub-key

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

LastPass credentials are used to retrieve a shared set of secrets
These secrets are then passed into Vault - used for Terraform and Helm secrets

## Vault paths
```
# GCE credentials JSON
/secret/terraform/$(GCE_PROJECT_ID)/auth['credentials']

# Kubeconfig secrets (used by Jenkins)
/secret/k8s_contexts/$(CONTEXT_NAME)

# Helm secrets, deployed via Landscaper
/secret/landscape/$(GIT_BRANCH)
```

## Troubleshooting

- Error messages
GCloud credentials failing
```
Failed to load backend:
Error configuring the backend "gcs": Failed to configure remote backend "gcs": google: could not find default credentials.
```

This means you don't have GOOGLE_CREDENTIALS set. Run `gcloud auth activate-service-account` to remedy.

- minikube clock out of sync
Fix:
```
minikube ssh -- docker run -i --rm --privileged --pid=host debian nsenter -t 1 -m -u -n -i date -u $(date -u +%m%d%H%M%Y)
```

- chartmuseum helm chart server
Requires command `gcloud auth application-default login` having been run. Mounts your own google credentials json inside of the chartmuseum container.
