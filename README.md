# Kubernetes desired-state configuration repo

Note: master branch is in development. Use a release for stability.

## Features
- Secrets pulled in from Hashicorp Vault
- Can be applied locally (via minikube) or in GCE (via kops)
- Use branches for different deployed apps / configs / secrets
- anything in namespace that's not in landscaper will be deleted
- deploys into a single project

# quick start
- clone this repo
- start local dev-vault container
```
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
```
- grab secrets with feed them into local vault
```
export VAULT_ADDR=http://127.0.0.1:8200
# grab an environment's secrets
# example: master branch (production) credentials
lpass show Shared-k8s/k8s-landscaper/master --notes
# copy above output and paste into your terminal
```
- install 'landscape' python tool (this repo)
```
cd landscape && pip install --upgrade landscape
```
- (minikube) run:
```
make PROVISIONER=minikube
```
- (gce) run:
```
make PROVISIONER=terraform GCE_PROJECT_ID=staging-123456
```

## Jenkins deployment
see Jenkinsfile in repo

## Features
 - Compare branches to compare environments
 - Sign off on production changes using GitHub approve workflow
 - Cluster's name is the branch of the repo's deployment. master=production
   example: landscaper deploys to staging-123456.
            the first cluster name in project may be master, the second dev, etc.
            each must be a separate branch of landscaper
## Core Charts
 - [common-chart](https://github.com/shaneramey/common-chart)
    defines templates that can be used by all charts
 - [monocular](https://github.com/shaneramey/helm-charts/tree/master/monocular)
    GUI to view installed/available charts
 - [jenkins](https://github.com/shaneramey/helm-charts/tree/master/jenkins)
    CI/CD workflow
 - [vault](https://github.com/shaneramey/helm-charts/tree/master/vault)
    back-end for Kubernetes secrets (including CA PKI)
 - [helm-chart-publisher](https://github.com/shaneramey/helm-charts/tree/master/helm-chart-publisher)
    curl-able API to publish Helm charts to a HTTP Helm chart repo
 - [openvpn](https://github.com/shaneramey/helm-charts/tree/master/openvpn)
    provides remote access
 - [nssetup](https://github.com/shaneramey/helm-charts/tree/master/nssetup)
    limits and other per-namespace setup (e.g., LimitRanges + ResourceQuotas)
 - [389ds](https://github.com/shaneramey/helm-charts/tree/master/389ds)
    LDAP server
 - [fluentd](https://github.com/shaneramey/helm-charts/tree/master/fluentd)
    DaemonSet to collect logs from each k8s node
 - [elasticsearch](https://github.com/shaneramey/helm-charts/tree/master/elasticsearch)
    StatefulSet with PersistentVolumeProvisioner support
 - [kibana](https://github.com/shaneramey/helm-charts/tree/master/kibana)
    deployment with LDAP login front-end
 - [heapster](https://github.com/shaneramey/helm-charts/tree/master/heapster)
    deployment with LDAP login front-end
 - [influxdb](https://github.com/shaneramey/helm-charts/tree/master/influxdb)
    deployment with LDAP login front-end

## Application Charts
 - [django](https://github.com/shaneramey/helm-charts/tree/master/django)
    defines templates that can be used by all charts
 - [nginx](https://github.com/shaneramey/helm-charts/tree/master/nginx)
    nginx front-end for services that auto-submits a CSR / loads TLS cert
 - [redis](https://github.com/shaneramey/helm-charts/tree/master/redis)
    defines templates that can be used by all charts
 - [postgresql](https://github.com/shaneramey/helm-charts/tree/master/postgresql)
    defines templates that can be used by all charts
 - [django-nginx-redis-postgresql](https://github.com/shaneramey/helm-charts/tree/master/django-nginx-redis-postgresql)
    chart that wraps (requires) django + nginx + redis + postgresql charts
 - [nodejs-nginx-redis-postgresql](https://github.com/shaneramey/helm-charts/tree/master/nodejs-nginx-redis-postgresql)
    chart that wraps (requires) nodejs + nginx + redis + postgresql charts

## Docs
 - [limitations](docs/limitations.md)
 - [prerequisites](docs/prerequisites.md)
 - [lastpass](docs/lastpass.md)
 - [forking](docs/forking.md)
 - [secrets](docs/secrets.md)
 - [deployment](docs/deployment.md)
 - [exposing jenkins to github behind nat](docs/exposing-jenkins-behind-nat.md)
 - [targets](docs/targets.md)
 - [pki](docs/pki.md)
 - [storageclasses](docs/storageclasses.md)
 - [init-containers](docs/init-containers.md)
 - [troubleshooting](docs/troubleshooting.md)
 - [design-doc](docs/design-doc.md)
 - [open-questions](docs/open-questions.md)

## Dependencies
Clone this repo, and install dependencies by running `make bootstrap`. This will install:
- [Kubernetes Helm](https://github.com/kubernetes/helm)
- [Landscaper](https://github.com/Eneco/landscaper)
- [envconsul](https://github.com/hashicorp/envconsul)
- [Hashicorp Vault](https://www.vaultproject.io) client `vault` command
- (optional) [lastpass-cli](https://github.com/lastpass/lastpass-cli) for secrets backups
- (minikube deploys) [minikube](https://github.com/kubernetes/minikube)
- (minikube deploys) [docker vault container](https://hub.docker.com/_/vault/)

## Wiping the cluster
WARNING: this will wipe out everything in your current KUBERNETES_CONTEXT! 

All data on your KUBERNETES_CONTEXT will be lost!

Make sure you're not running this against the wrong target!

Decommission cluster:
```
make PURGE_ALL=yes purge
```

## HTTP Proxy configuration
wiping out minikube and re-restarting it from scratch means pulling all of the docker images inside of the cluster.

To set a proxy for the docker daemon, you can set environment variables in your shell. Then run `make` and they will show in the `minikube start` command.

Example, MacOS:
```
DEFAULT_INTERFACE=`netstat -rn | grep default | head -n 1 | awk '{ print $NF }'`
DEFAULT_IP=`ifconfig $DEFAULT_INTERFACE | grep inet | awk '{ print $2 }'`
export HTTPS_PROXY=http://${DEFAULT_IP}:3128
export HTTP_PROXY=http://${DEFAULT_IP}:3128
```

## TODO
currently vault reads in all values to env vars. In the future the env vars to
be read from Vault should be selected from the Landscaper yaml definition of the secrets