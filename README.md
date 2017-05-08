# Landscape
Kubernetes cluster desired-state configuration repo

Features:
Compare branches to compare environments!
Use GitHub workflow to approve environment changes
fork off branches of current environments for testing or staging upgrades

Principles:
- Single point of control (branches of this repo) as Kubernetes deployments.
- Prevent configuration sprawl by supplying "building blocks" (Helm Charts)

Limitations:
- Chart names can only be deployed once per namespace
   to conform to the structure of vault and landscaper
   Example: there must only be one `nginx` chart in namespace `myapp`
- Each cluster gets its own cluster domain (in /etc/resolv.conf on each pod and external calls to services). FIXME: explain this

## Core Charts
 - [common-chart](https://github.com/shaneramey/common-chart)
       defines templates that can be used by all charts
 - [vault](https://github.com/shaneramey/helm-charts/tree/master/vault)
      back-end for Kubernetes secrets (including CA PKI)
 - [cfssl](https://github.com/shaneramey/helm-charts/tree/master/cfssl)
      optional;alternatively use k8s CertificateSigningRequests for auto-signing
 - [nssetup](https://github.com/shaneramey/helm-charts/tree/master/nssetup)
      Provides per-namespace resources (e.g., LimitRanges + ResourceQuotas)
 - [389ds](https://github.com/shaneramey/helm-charts/tree/master/389ds)
      LDAP server
 - [nginx](https://github.com/shaneramey/helm-charts/tree/master/nginx)
      nginx front-end for services that auto-submits a CSR / loads TLS cert
 - [helm-chart-publisher](https://github.com/shaneramey/helm-charts/tree/master/helm-chart-publisher)
      curl-able API to publish Helm charts to a HTTP Helm chart repo
 - [monocular](https://github.com/shaneramey/helm-charts/tree/master/monocular)
      GUI to view installed/available charts
 - [jenkins](https://github.com/shaneramey/helm-charts/tree/master/jenkins)
      back-end for secrets
 - [fluentd](https://github.com/shaneramey/helm-charts/tree/master/fluentd)
      DaemonSet to collect logs from each k8s node
 - [elasticsearch](https://github.com/shaneramey/helm-charts/tree/master/elasticsearch)
      PetSet with PersistentVolumeProvisioner support
 - [kibana](https://github.com/shaneramey/helm-charts/tree/master/kibana)
      Deployment with LDAP login front-end
 - [openvpn](https://github.com/shaneramey/helm-charts/tree/master/openvpn)
      Provides remote access
 - [heapster](https://github.com/shaneramey/helm-charts/tree/master/heapster)
      Deployment with LDAP login front-end
 - [influxdb](https://github.com/shaneramey/helm-charts/tree/master/influxdb)
      Deployment with LDAP login front-end

## Application Charts
 - [postgresql](https://github.com/shaneramey/helm-charts/tree/master/postgresql)
       defines templates that can be used by all charts
 - [redis](https://github.com/shaneramey/helm-charts/tree/master/redis)
       defines templates that can be used by all charts
 - [django](https://github.com/shaneramey/helm-charts/tree/master/django)
       defines templates that can be used by all charts
 - [django-nginx-redis-postgresql](https://github.com/shaneramey/helm-charts/tree/master/django-nginx-redis-postgresql)
       Chart that wraps (requires) django + nginx + redis + postgresql charts
 - [nodejs-nginx-redis-postgresql](https://github.com/shaneramey/helm-charts/tree/master/nodejs-nginx-redis-postgresql)
       Chart that wraps (requires) nodejs + nginx + redis + postgresql charts

## Why use Helm?
Helm is [an official Kubernetes](https://github.com/kubernetes/helm) package manager

Its strength is reusing and retooling config files
It promotes separation of concerns (secrets are external from Helm configs)

# Rapid iteration of Chart development
preferred method is CI system (Jenkins), for version-control/GitHub approval
this works great for local development of Charts
```
git clone https://github.com/shaneramey/helm-charts
cd helm-charts
helm upgrade nginx --namespace=jenkins nginx # near-instantaneous
```

# More about Helm

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

It handles deletes of objects by wiping out everything in the namespace that's not defined in Landscape.

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

see [minikube.sh](minikube.sh)

# minikube: selective deployment

If you don't want to deploy all namespaces/charts in the current branch
Here's the interesting part of how it works. You can pull this into a shell script
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

## Secrets
Secrets are pulled from Vault via [envconsul](envconsul.io) via `landscaper apply`.
Environment variables pulled from Vault are prefixed with the string "SECRET_".
This is to prevent overriding root user environment variables, for security reasons.
Landscape `secrets` must use a 'secret-' prefix in their names.

## Prerequisite install steps
### Landscaper
```
wget https://github.com/Eneco/landscaper/releases/download/1.0.1/landscaper-v1.0.1-linux-amd64
sudo mv landscaper-v1.0.1-linux-amd64 /usr/local/bin/landscaper
```

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
- add trusted cert to MacOS
```
sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" "/tmp/ca.pem"
```

## MiniKube Setup
```
# start minikube
minikube start --kubernetes-version=v1.6.0 --extra-config=kubelet.ClusterDomain=downup.local --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC
minikube addons enable registry-creds
```

### ImagePullSecrets (Kubernetes Cluster Setup)
Download service account JSON from GCR and run:
```
kubectl create secret docker-registry gcr-json-key --docker-server=https://us.gcr.io --docker-username=_json_key --docker-password="$(cat ~/Downloads/downup-3baac25cc60e.json)" --docker-email=shane.ramey@gmail.com
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}'
```

# Install Helm Tiller into Kubernetes cluster
```
helm init
```

## Deployment pipeline
via Jenkinsfile
- Checkout
- Environment (Secrets)
- Build
- Test
- Tag
- Publish
- Deploy

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

### Secrets: certificate signing
Two methods, current (cfssl) and future (Kubernetes-native)
See an example of certificate requests/signing in the "nginx" helm chart at http://charts.downup.us/

cfssl
- pass `--cluster-signing-cert-file` and `--cluster-signing-key-file` to kube-controller-manager
   - default values are /etc/kubernetes/ca/ca.pem and /etc/kubernetes/ca/ca.key
- run `kubectl certificate approve http.jenkins.svc.cluster.local`
- run `kubectl get csr http.jenkins.svc.cluster.local -o jsonpath='{.status.certificate}' | base64 -D > server.crt`

Kubernetes-native
- pass `--cluster-signing-cert-file` and `--cluster-signing-key-file` to kube-controller-manager
   - default values are `/etc/kubernetes/ca/ca.pem` and `/etc/kubernetes/ca/ca.key`
- run `kubectl certificate approve http.mynamespace.svc.cluster.local`
- run `kubectl get csr http.mynamespace.svc.cluster.local -o jsonpath='{.status.certificate}' | base64 -D > server.crt`

### Secrets naming convention
This is to prevent overrides of the root user's environment variables, a practice to promote stability

# Secrets usage
 - by way of Helm via a ConfigMap attached to an init-container named `init-setup`
 - using secretKeyRef: in a k8s definition yaml file

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

# Auto signing certificate requests
Get list of pending certificates
```
kubectl get csr | grep -v NAME  | awk '{ print $1 }' | grep Pending 
```
