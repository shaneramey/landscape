see [minikube.sh](minikube.sh)

# minikube: selective deployment

If you don't want to deploy all namespaces/charts in the current branch
Here's the interesting part of how it works. You can pull this into a shell script
```
# Deploy Jenkins chart into Jenkins namespace into Kubernetes
CHART_NAME=jenkins
K8S_NAMESPACE=jenkins
GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

## Jenkins jobs (WIP)
# - deploy entire landscape to kubeconfig context
# - wipe namespace: make PURGE_ALL=yes K8S_NAMESPACE=nginx purge

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

# MiniKube LoadBalancer implementation
if you create a service of type LoadBalancer: instead of using a cloud-provisioned instance, it is instead accessible via NodePorts on minikube's `minikube ip`

Example:

Expose the service
```
kubectl expose svc http --name=lbhttp --type=LoadBalancer
```

Access the service
```
kubectl get svc lbhttp
NAME      CLUSTER-IP   EXTERNAL-IP   PORT(S)         AGE
lbhttp    10.0.0.227   <pending>     443:31676/TCP   <invalid>
```

The service is then available at https://`minikube ip`:31676

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
