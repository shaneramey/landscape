# Landscape
Desired-State configuration for a deployed Kubernetes Stack
https://github.com/shaneramey/landscape

## Requirements
- helm
- landscaper
- envconsul
- Hashicorp Vault

## Setup
```
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | awk -F ': ' '{ print $2 }'`
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
helm repo add charts.downup.us http://charts.downup.us
```

## How to use
Environment deployments (master branch is customer-facing, by convention)
 - fork the 'base' branch from https://github.com/shaneramey/landscape
 - updates to 'base' branch can be merged into feature branches

then, compare branches to compare environments!
Use GitHub workflow to approve environment changes
fork off branches of current environments and go wild!

reusing and retooling config files is where Helm's real strength is
https://news.ycombinator.com/item?id=14078838

## MiniKube Setup
```
# start minikube
minikube start --kubernetes-version=v1.6.0 --extra-config=kubelet.ClusterDomain=downup.local
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

## Secrets
Secrets are passed into `landscaper apply` via envconsul. 
To prevent overriding root user environment variables, environment variables pulled from Vault are prefixed with the string "SECRET_".

### Secrets passage from Vault to Kubernetes
The path from Vault to Kubernetes configuration files is:
vault secrets
    -> envconsul
        -> environment variables
            -> landscape
                -> helm
		            -> init-container w/ configmap template
		                -> template replacement with env variables
		                    -> configuration file with secrets populated

### Vault component of secrets
Hashicorp Vault keys are prefixed with the path:
```
/secret/landscape/$(KUBERNETES_CONTEXT)/$(KUBERNETES_NAMESPACE)/$(HELM_CHARTNAME)/
```

To test this, run:
```
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
```

You should see output like:
```
SECRET_USERNAME=foobar
SECRET_PASSWORD=barbaz
```

### Example walk-through
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

The init-container looks like this:
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
Landscape `secrets` must use a 'secret-' prefix in their names. Example:
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
``

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
