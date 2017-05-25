# kops

## DNS

### CoreDNS controller
The dns-controller recognizes annotations on nodes. They are used to specify whether an internal or external dns record is made for the service or node.

### labels
dns.alpha.kubernetes.io/external will set up records for accessing the resource externally

dns.alpha.kubernetes.io/internal will set up records for accessing the resource internally

The syntax is a comma separated list of fully qualified domain names.

When added on Service controllers:

dns.alpha.kubernetes.io/external creates a Route53 A record with public IPs of all the nodes dns.alpha.kubernetes.io/internal creates a Route53 A record with private IPs of all the nodes

https://github.com/kubernetes/kops/blob/master/dns-controller/README.md

## Getting started

Define your cluster state store (must be in S3 or GFS or local minio server)
```
export KOPS_STATE_STORE=s3://clusterstate2

### AWS
```
kops create cluster --admin-access=`curl http://ipecho.net/plain`/32 --associate-public-ip=true --authorization=RBAC --cloud=aws --cloud-labels=shane=ramey --dns=public  --networking=calico --node-count=1 --target=terraform --name=test6.downup.us --zones=us-west-2a --dns-zone=downup.us
```
### vSphere
see https://github.com/kubernetes/kops/blob/master/docs/development/vsphere-dev.md
```
KOPS_FEATURE_FLAGS=+VSphereCloudProvider kops create cluster --admin-access=`curl http://ipecho.net/plain`/32 --associate-public-ip=true --authorization=RBAC --cloud=vsphere --cloud-labels=shane=ramey --dns=public  --networking=calico --node-count=1 --target=terraform --zones=us-west-2a --dns-zone=downup.us --name=test7.downup.us


      --vsphere-coredns-server string        vsphere-coredns-server is required for vSphere.
      --vsphere-datacenter string            vsphere-datacenter is required for vSphere. Set the name of the datacenter in which to deploy Kubernetes VMs.
      --vsphere-datastore string             vsphere-datastore is required for vSphere.  Set a valid datastore in which to store dynamic provision volumes.
      --vsphere-resource-pool string         vsphere-resource-pool is required for vSphere. Set a valid Cluster, Host or Resource Pool in which to deploy Kubernetes VMs.
      --vsphere-server string                vsphere-server is required for vSphere. Set vCenter URL Ex: 10.192.10.30 or myvcenter.io (without https://)
```

To apply, choose one of the above cloud providers and run:
```
cd out/terraform/
terraform plan
terraform apply
terraform destroy
```

# Not verified to work:

kops create cluster --admin-access=`curl http://ipecho.net/plain` --associate-public-ip=true --authorization=RBAC --cloud=gce --cloud-labels=shane=ramey --dns=public  --dns-zone=shane.local --networking=calico --node-count=1 --target=terraform


# ca.crt - provided by GKE (can't override?)
gcloud container clusters create __CLUSTER_NAME__ \
  --disk-size 500 \
  --zone __CLUSTER_ZONE__ \
  --enable-cloud-logging \
  --enable-cloud-monitoring \
  --machine-type n1-standard-2 \
  --num-nodes 3 \
  --network __NETWORK__ \
  --node-labels=__K8s_NODE_LABELS__ \
  --tags=__GCE_NODE_TAGS__


/opt/kubernetes/bin/kube-apiserver --cloud-provider=vsphere --cloud-config=/etc/cloud.conf --apiserver-count=3 --client-ca-file=/etc/kubernetes/ssl/cachain.crt --service-cluster-ip-range=10.100.0.0/20 --bind-address=0.0.0.0 --tls-cert-file=/etc/kubernetes/ssl/apiserverfqdn.crt --tls-private-key-file=/etc/kubernetes/ssl/apiserverfqdn.key --service-account-key-file=/etc/kubernetes/ssl/clientaccess.key --authorization-mode=RBAC --authorization-rbac-super-user=clientaccess --runtime-config=authorization.k8s.io/v1beta1=true,extensions/v1beta1/networkpolicies,extensions/v1beta1/apps=true --admission-control=NamespaceLifecycle,LimitRanger,ServiceAccount,ResourceQuota --secure-port=443 --etcd-cafile=/etc/etcd/ssl/root-ca.crt --etcd-certfile=/etc/etcd/ssl/clientaccess.crt --etcd-keyfile=/etc/etcd/ssl/clientaccess.key --etcd-servers=https://etcd1:2379,https://etcd2:2379,https://etcd3:2379 --allow-privileged=true --log-dir=/var/log/kubernetes --logtostderr=false --v=2

/opt/kubernetes/bin/kube-controller-manager --cloud-provider=vsphere --cloud-config=/etc/cloud.conf --leader-elect=true --root-ca-file=/etc/kubernetes/ssl/root-ca.crt --service-account-private-key-file=/etc/kubernetes/ssl/clientaccess.key --kubeconfig=/var/lib/kubelet/kubeconfig --log-dir=/var/log/kubernetes --logtostderr=false --v=2
root      1371     1  0 Apr11 ?        00:33:03 /opt/kubernetes/bin/kube-scheduler --leader-elect=true --kubeconfig=/var/lib/kubelet/kubeconfig --log-dir=/var/log/kubernetes --logtostderr=false --v=2

/opt/kubernetes/bin/kube-proxy --kubeconfig=/var/lib/kubelet/kubeconfig --proxy-mode=iptables --masquerade-all=true --log-dir=/var/log/kubernetes --logtostderr=false --v=2

/opt/kubernetes/bin/kubelet --cloud-provider=vsphere --cloud-config=/etc/cloud.conf --kubeconfig=/var/lib/kubelet/kubeconfig --api-servers=https://apiserver-loadbalancer --cluster-dns=10.100.0.10 --cluster-domain=cluster.local --enable-server --pod-manifest-path=/etc/kubernetes/manifests --network-plugin=cni --network-plugin-dir=/etc/cni/net.d --tls-cert-file=/etc/kubernetes/ssl/apiserverfqdn.crt --tls-private-key-file=/etc/kubernetes/ssl/apiserverfqdn.key --resolv-conf= --allow-privileged=true --log-dir=/var/log/kubernetes --logtostderr=false --v=2

TLS/auth parameters
 - apiserver
   - client-ca-file
   - tls-cert-file
   - tls-private-key-file
   - service-account-key-file
   - etcd-cafile
   - etcd-certfile
   - etcd-keyfile
 - controller-manager
   - root-ca-file
   - service-account-private-key-file
   - kubeconfig
- scheduler
   - kubeconfig
- kube-proxy
   - kubeconfig
- kubelet
   - kubeconfig

Network parameters
- apiserver
  - service-cluster-ip-range
- kube-proxy
  - masquarade-all
- kubelet
  - cluster-dns
  - cluster-domain
  - network-plugin
  - resolv-conf

Other parameters
- kubernetes-apiserver
  - allow-privileged
- kubelet
  - allow-privileged

Container parameters
- apiserver
  - allow-provileged

Other considerations
- kubernetes federation
