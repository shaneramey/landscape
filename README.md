# landscape: portable Kubernetes clusters + charts

## Features
Deploy k8s clusters + apps (Helm Charts) to:
- minikube
- GKE
- Any other Kubernetes cluster to which you have credentials

It does this in a portable way, by abstracting cluster provisioning, and centralizing secrets in Vault

Apps are deployed via Helm Charts, with secrets kept in Vault until deployment

## Arguments
```
$ landscape --help
landscape: Provisions Kubernetes clusters and Helm charts, with secrets in Hashicorp Vault.

Operates on a single cloud, minikube, or GCE project at a time

A "cloud" is a single GCE project, or minikube
A "cluster" is a Kubernetes cluster
There may be multiple kubernetes "clusters" within a cloud

Usage:
  landscape cloud list [--cloud-provisioner=<cloud_provisioner>]
  landscape cloud converge [--cloud=<cloud_project>]
  landscape cluster list [--cloud=<cloud_project>] [--cloud-provisioner=<cloud_provisioner>]
  landscape cluster converge --cluster=<cluster_name> [--converge-cloud]
      [--tf-templates-dir=<tf_templates_dir> ] [--debug]
  landscape cluster environment (--write-kubeconfig|--read-kubeconfig) [--kubeconfig-file=<kubecfg>]
  landscape charts list --cluster=<cluster_name> [--provisioner=<cloud_provisioner>]
  landscape charts converge --cluster=<cluster_name> [--chart-dir=<path containing chart defs>]
      [--namespaces=<namespace>] [--converge-cluster] [--converge-cloud] [--git-branch=<branch_name>]
  landscape prerequisites install

Options:
  --cloud-provisioner=<cloud_provisioner>      Cloud provisioner ("terraform" or "minikube")
  --cluster=<context_name>                     Operate on cluster context, defined in Vault
  --git-branch=<branch_name>                   Git branch to use for secrets lookup
  --write-kubeconfig                           Write ~/.kube/config with contents from Vault
  --read-kubeconfig                            Read ~/.kube/config and put its contents in Vault
  --kubeconfig-file=<kubecfg>                  Specify path to KUBECONFIG [default: ~/.kube/config-landscaper].
  --cloud=<cloud_project>                      k8s cloud provisioner.
  --project=<gce_project_id>                   in GCE environment, which project ID to use. [default: minikube].
  --kubernetes-version=<k8s_version>           in GCE environment, which project ID to use [default: 1.7.0].
  --cluster-dns-domain=<dns_domain>            DNS domain used for inside-cluster DNS [default: cluster.local].
  --minikube-driver=<driver>                   (minikube only) driver type (virtualbox|xhyve) [default: virtualbox].
  --switch-to-cluster-context=<boolean>        switch to kubernetes context after cluster converges [default: true].
  --namespaces=<namespace>                     install only charts under specified namespaces (comma-separated).
  --fetch-lastpass                             Fetches values from Lastpass and puts them in Vault
  --tf-templates-dir=<tf_templates_dir>        Terraform templates directory [default: ./tf-templates].
  --chart-dir=<path containing chart defs>     Helm Chart deployment directory [default: ./charts].
  --debug                                      Run in debug mode.
Provisioner can be one of minikube, terraform.
```

## Getting started

Set up is same for minikube and GKE
1. clone this repo
```
git clone git@github.com:oreillymedia/landscape.git
```

2. cd into the repo and install landscape CLI tool
```
cd landscape
python3 -m venv ~/venv && \
source ~/venv/bin/activate && \
pip install --upgrade .
```

3. Put the secrets from LastPass into your local Vault.
```
lpass login username@domain.account
lpass show Shared-k8s/k8s-landscaper/master --notes
```

## Cluster-specific provisioning

### minikube

- Converge cluster and charts
```
make
```

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
make CLUSTER_NAME=gke_staging-165617_us-west1-a_master
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
