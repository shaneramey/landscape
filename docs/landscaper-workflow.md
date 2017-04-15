# Landscaper workflow

## Quick start
```
git clone https://github.com/shaneramey/landscape
export VAULT_ADDR=<Vault Server IP>
git checkout `<environment_branch`>
# deploys to your $KUBECONFIG current-context
# DANGER: don't do this unless you want to make changes to your kubernetes cluster!
# make deploy
```

## Prerequisites
- [Helm](https://github.com/kubernetes/helm)
- [Landscaper](https://github.com/Eneco/landscaper)
- [Helm Local Bump plugin](https://github.com/shaneramey/helm-local-bump)

Steps: Run helm-chart-publisher (should be in your landscape)

helm install .
# make changes to repo
helm upgrade fantastic-lamb .

- Gotta check this out man... dude bro

# Why Helm
- Leverage community to solve the deployment problem
- Community charts
- One repo to represent cluster state

it's all a roll-up

Helm Chart release names are by convention unique

Benefits:
 - not randomly-generate release names allows updating
    `helm upgrade -i kube-system-nginx ./helm/nginx --namespace=myapp`
 - rolls up into landscaper:
    `landscaper apply --dir kube-system

Branches:
 - downup: deploys
 - test: runs helm install --dry-run


# Push a Helm Chart to a chart repository
using https://github.com/luizbafilho/helm-chart-publisher

Steps:
- start API daemon
```
PORT=8080 helm-chart-publisher --config helm-chart-publisher-config.yaml
```

where helm-chart-publisher-config.yaml is something like:
```
repos:
  - name: downup
    bucket: charts.downup.us

storage:
  s3:
    accessKey: __AWS_ACCESS_KEY_ID__
    secretKey: __AWS_SECRET_ACCESS_KEY__
    region: us-west-2
    bucket: charts.downup.us
```

- upload chart
```
$ curl -i -X PUT -F repo=downup -F chart=@$HOME/nfs-provisioner-0.1.0.tgz http://localhost:8080/charts
```

# NOTE: must manually bump version in Chart.yaml!

then you can:

helm repo add charts.downup.us http://charts.downup.us

CI/CD steps
```
cd helm
helm upgrade -i nfs-provisioner ./helm/nfs-provisioner/ --namespace=kube-system --set defaultStorageClass=true

helm upgrade -i nginx ./helm/nginx/ --namespace=newnamespace

helm install nginx ./nginx/ --namespace=newnamespace

npm install helm-chart-s3-publisher@1.0.0
helm-chart-publisher -a $AWS_ACCESS_KEY_ID -s $AWS_SECRET_ACCESS_KEY -b charts.downup.us -r us-west-2 &
# TODO: k8s syntax ACCESSKEY=123xyz099 SECRETKEY=098abc211 BUCKET=chart-repo helm-chart-publisher

Need to add IAM user with s3 policies (TODO: enumerate list of rights needed)

# keep data
edit pvc after it's provisioned and set persistentVolumeReclaimPolicy


# Time bomb functionality could be added
set attribute to delete, when landscaper runs it gets removed
helm delete nfs-provisioner --purge

## Charts repo bootstrap
If setting up an initial Helm Charts repo, run helm-chart-publisher locally
PORT=8081 helm-chart-publisher -c /Users/sramey/helm-chart-publisher-config.yaml

Note: this doesn't apply if you've deployed the chart charts.downup.us/helm-charts-publisher to your cluster