# Landscape
Kubernetes cluster desired-state configuration repo

Features:
Compare branches to compare environments!
Use GitHub workflow to approve environment changes
fork off branches of current environments for testing or staging upgrades

Principles:
- Single point of control (branches of this repo) as Kubernetes deployments.

## Why use Helm?
Helm is [an official Kubernetes](https://github.com/kubernetes/helm) package manager

Its strength is reusing and retooling config files
It promotes separation of concerns (secrets are external from Helm configs)

Helm claims to be "the best way to find, share, and use software built for Kubernetes".
A quote from the Helm README:
> Use Helm to...
> Find and use popular software packaged as Kubernetes charts
> Share your own applications as Kubernetes charts
> Create reproducible builds of your Kubernetes applications
> Intelligently manage your Kubernetes manifest files
> Manage releases of Helm packages

It has a vibrant developer community and a highly-active Slack channel

[Here is a repo of Landscape-compatible Helm Charts](https://github.com/shaneramey/helm-charts)

## Why use Landscape?
Landscape is currently the easiest way to define and enforce all Helm charts in a Kubernetes cluster.
It provides a single point of control (branches of this repo) as Kubernetes deployments.
Landscape implements the Features listed above painlessly.

The Landscape project itself currently has a much smaller fan-base than Helm.
This may be because it was only recently introduced, and is gaining traction.
Some or all of its functionality may be pulled into Helm eventually.

## Deployment targets:
 - local (minikube)
 - GKE
 - Any Kubernetes environment/context with a "default" StorageClass

## Requirements
- [Kubernetes Helm](https://github.com/kubernetes/helm)
- [Landscaper](https://github.com/Eneco/landscaper)
- [envconsul](https://github.com/hashicorp/envconsul)
- [Hashicorp Vault](https://www.vaultproject.io) client `vault` command
- (minikube deploys) [minikube](https://github.com/kubernetes/minikube)
- (minikube deploys) [docker vault container](https://hub.docker.com/_/vault/)

## Quick Start
Generate a minikube k8s/landscape/helm/vault environment

Just copy and paste this into a terminal (tested on MacOS)
```
# Start local Kubernetes environment w/ Helm
minikube start --kubernetes-version=v1.6.0 \
  --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
  --cpus 4 \
  --disk-size 20g \
  --memory 4096
  # set --docker-env to run minikube on a remote docker host
minikube addons enable registry-creds # log in to your private registries
helm init

# Set up local Vault backend
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
export VAULT_ADDR=http://127.0.0.1:8200
unset VAULT_TOKEN # auth doesnt work unless this is unset
vault auth `docker logs dev-vault 2>&1 | \
  grep '^Root\ Token' | awk -F ': ' '{ print $2 }' | tail -n 1`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)

# Add Helm Chart Repo
helm repo add charts.downup.us http://charts.downup.us

# Choose which branch you want to deploy
# the master branch represents the customer-facing env, by convention
git checkout branch_i_want_to_deploy

# First time only: Populate secrets
make setsecrets # you'll be guided through adding/editing secrets
## TIP: copy the produced `vault write` statements to a LastPass Secure Note

# Set Kubernetes context
kubectl config use-context minikube # or cluster1, cluster2, etc.

# Deploy environment
make deploy # deploy current branch to $KUBERNETES_CONTEXT

# Don't want to deploy everything in the full branch? run:
```
# Deploy Jenkins chart into Jenkins namespace into Kubernetes
CHART_NAME=jenkins
K8S_NAMESPACE=jenkins
GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

# Read secrets from Hashicorp Vault
gsed -i "s/__GIT_BRANCH__/$GIT_BRANCH/g" envconsul-config.hcl.tmpl > envconsul-config.hcl
gsed -i "s/__K8S_NAMESPACE__/$K8S_NAMESPACE/g" envconsul-config.hcl
gsed -i "s/__HELM_CHART__/$CHART_NAME/g" envconsul-config.hcl
envconsul -config="./envconsul-config.hcl" -secret="/secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME" -once -retry=1s -pristine -upcase env

# Apply landscape
landscaper apply --dir $K8S_NAMESPACE/$CHART_NAME/ --namespace=$K8S_NAMESPACE
```

### minikube-only: cluster ip routing
sudo route add 10.0.0.0/20 `minikube ip`

## Secrets
Secrets are pulled from Vault via [envconsul](envconsul.io) via `landscaper apply`.
Environment variables pulled from Vault are prefixed with the string "SECRET_".
This is to prevent overriding root user environment variables, for security reasons.

## Prerequisite install steps
```
# Install Landscaper
brew install glide
cd $GOPATH
mkdir -p src/github.com/eneco/
cd !$
git clone git@github.com:shaneramey/apps.git
mv apps/landscaper .
cd landscaper
make bootstrap build
sudo mv build/landscaper /usr/local/bin

### Envconsul
wget https://releases.hashicorp.com/envconsul/0.6.2/envconsul_0.6.2_darwin_amd64.tgz
tar zxvf envconsul_0.6.2_darwin_amd64.tgz
sudo mv envconsul /usr/local/bin/

### Helm
# NOTE: Temporary k8s 1.6.1 workaround needed: https://github.com/kubernetes/helm/issues/2224

docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
export VAULT_ADDR=http://127.0.0.1:8200
vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | tail -n 1 | awk -F ': ' '{ print $2 }'`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
helm repo add charts.downup.us http://charts.downup.us
```

## How to use
Each branch represents an environment desired-state configuration.
The branches can be deployed to multiple cluster destinations.
The only unique part about each branch deployment are the secrets, which are pulled from Vault.
master branch is customer-facing, by convention

## TODO
- Running the bootstrap vault container within the cluster is untested
   The cluster must bootstrap from an external Vault

## MiniKube Setup
```
# start minikube
minikube start --kubernetes-version=v1.6.0 --extra-config=kubelet.ClusterDomain=downup.local --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC
# gcr credentials
kubectl create secret docker-registry gcr-json-key --docker-server=https://us.gcr.io --docker-username=_json_key --docker-password="$(cat ~/Downloads/downup-3baac25cc60e.json)" --docker-email=shane.ramey@gmail.com
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
helm init
```

## Base branch
 - Contains base charts
 - Deployed from  "base" branch:
    - charts.downup.us/nfs-provisioner: AutoProvision "nfs" and "default" StorageClasses
    - charts.downup.us/helm-chart-publisher
    - charts.downup.us/openvpn
    - stable/jenkins: Used to deploy Helm Landscape

### Secrets passage from Vault to Kubernetes
The path from Vault to Kubernetes configuration files is:
vault secrets
     envconsul
        -> environment variables
            -> landscape
              -> helm
		          -> init-container w/ configmap template
		              -> template replacement with env variables
		                -> configuration file with secrets populated

### Vault structure of secrets
Hashicorp Vault keys are prefixed with the path:
```
/secret/landscape/$(KUBERNETES_CONTEXT)/$(KUBERNETES_NAMESPACE)/$(HELM_CHARTNAME)/
```

### Envconsul expansion example

```
NAMESPACE=somenamespace
CHART_NAME=somehelmchart
GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`
vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | awk -F ': ' '{ print $2 }'`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
vault write /secret/landscape/$(GIT_BRANCH)/$(NAMESPACE)/$CHART_NAME) username=foobar password=barbaz
cat <<EOF > configtest.hcl
vault {
  address = "http://127.0.0.1:8200"
  renew  = false
}

secret {
  no_prefix = true
  path   = "/secret/$(GIT_BRANCH)/$(NAMESPACE)/$CHART_NAME)"
  format = "SECRET_{{ key }}"

}
EOF

envconsul -config="./configtest.hcl" -secret="/secret/landscape/$(GIT_BRANCH)/$(NAMESPACE)/$CHART_NAME)" -pristine -upcase env
# You should see output like:
#
# SECRET_USERNAME=foobar
# SECRET_PASSWORD=barbaz
```

### Helm Charts


#### init-containers
init-containers are widely used in the Landscape-compatible Helm Charts repo
init-containers are typically used for the following:
- substitute secrets into Helm templates
- generate TLS certificate signing requests (CSRs), and place them on the filesystem
- Other pre-application-container initialization

Example configmap in an init chart:
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: secrets-inject
  labels:
    chart: "{{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}"
data:
  init.sh:
    #! /bin/sh
    sed -e 's/__SECRET_HELLO_NAME__/$SECRET_HELLO_NAME/g' hello-secret.config.tmpl  > /post-secrets/hello-secret.config
    sed -ie 's/__SECRET_HELLO_AGE__/$SECRET_HELLO_AGE/g' /post-secrets/hello-secret.config
  hello-secret.config.tmpl:
    hello:
      age: "__SECRET_HELLO_AGE__"
      name: "__SECRET_HELLO_NAME__"
```

An example init-container looks like this:

```
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  template:
    metadata:
      annotations:
        pod.alpha.kubernetes.io/init-containers: '[
            {
                "name": "subst-config-secrets",
                "image": "busybox:latest",
                "command": ["/secrets-conversion/init.sh"],
                "workingDir": "/initial-certificate-store",
                "volumeMounts": [
                  {
                    "name": "replace-secrets",
                    "mountPath": "/pre-secrets"
                  },
                  {
                    "name": "workdir",
                    "mountPath": "/post-secrets"
                  }
                ]
            }
        ]'
    spec:
      containers:
      - name: myapp
        image: myapp:1.0
        command: ["/bin/myapp", "-c", "/config/hello-secret.config"]
        volumeMounts:
        - name: workdir
          mountPath: /config
      volumes:
        - name: workdir
          emptyDir: {}
        - name: replace-secrets
          configMap:
            name: secrets-inject
            defaultMode: 0755
            items:
            - key: init.sh
              path: init.sh
            - key: hello-secret.config.tmpl
              path: hello-secret.config.tmpl
```

### Secrets naming convention
Landscape `secrets` must use a 'secret-' prefix in their names.
This is to prevent overrides of the root user's environment variables, a practice to promote stability

Example:
```
name: secretive
release:
  chart: local/hello-secret:0.1.0
  version: 0.1.0
configuration:
  message: Hello, Landscaped world!
secrets:
  - secret-hello-name
  - secret-hello-age
```

These environment-variable values (from Vault) are pulled into Kubernetes Secrets by way of Helm via a ConfigMap attached to an init-container:

### ImagePullSecrets (Kubernetes Cluster Setup)
Download service account JSON from GCR and run:
```
kubectl create secret docker-registry gcr-json-key --docker-server=https://us.gcr.io --docker-username=_json_key --docker-password="$(cat ~/Downloads/downup-3baac25cc60e.json)" --docker-email=shane.ramey@gmail.com
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
```

### Open questions
- How can we generate a helm starter chart by prompting the user, such as:
```
Number of containers? [1] 3
  Container 1: number of volume mounts [0]
    Volume mount 1 name: ["volmount1"]
```

If this were possible, it might allow dynamically generated helm charts (just plug in your app)

### Troubleshooting
If values aren't updating with a script like:
```
kubectl delete secret helm-chart-publisher-helm-chart-publisher ; make -C ../apps/helm-chart-publisher publish_helm && helm repo update && helm local_bump -f helm-chart-publisher/helm-chart-publisher/helm-chart-publisher.yaml --patch && make deploy

make -C ../helm-charts/ publish_helm && helm repo update && helm local_bump -f openvpn/openvpn/openvpn.yaml --patch && make deploy
```
Try:
```
helm delete helm-chart-publisher-helm-chart-publisher  --purge
```
