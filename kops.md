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


/opt/kubernetes/bin/kube-apiserver --cloud-provider=vsphere --cloud-config=/etc/cloud.conf --apiserver-count=3 --client-ca-file=/etc/kubernetes/ssl/sbo-cachain.crt --service-cluster-ip-range=10.100.0.0/20 --bind-address=0.0.0.0 --tls-cert-file=/etc/kubernetes/ssl/k8s-seb1.dev.safaribooks.com.crt --tls-private-key-file=/etc/kubernetes/ssl/k8s-seb1.dev.safaribooks.com.key --service-account-key-file=/etc/kubernetes/ssl/client.dev-seb.local.key --authorization-mode=RBAC --authorization-rbac-super-user=client.dev-seb.local --runtime-config=authorization.k8s.io/v1beta1=true,extensions/v1beta1/networkpolicies,extensions/v1beta1/apps=true --admission-control=NamespaceLifecycle,LimitRanger,ServiceAccount,ResourceQuota --secure-port=443 --etcd-cafile=/etc/etcd/ssl/sbo-root-ca.crt --etcd-certfile=/etc/etcd/ssl/client.dev-seb.local.crt --etcd-keyfile=/etc/etcd/ssl/client.dev-seb.local.key --etcd-servers=https://k8s-seb1.dev.safaribooks.com:2379,https://k8s-seb2.dev.safaribooks.com:2379,https://k8s-seb3.dev.safaribooks.com:2379 --allow-privileged=true --log-dir=/var/log/kubernetes --logtostderr=false --v=2

/opt/kubernetes/bin/kube-controller-manager --cloud-provider=vsphere --cloud-config=/etc/cloud.conf --leader-elect=true --root-ca-file=/etc/kubernetes/ssl/sbo-root-ca.crt --service-account-private-key-file=/etc/kubernetes/ssl/client.dev-seb.local.key --kubeconfig=/var/lib/kubelet/kubeconfig --log-dir=/var/log/kubernetes --logtostderr=false --v=2
root      1371     1  0 Apr11 ?        00:33:03 /opt/kubernetes/bin/kube-scheduler --leader-elect=true --kubeconfig=/var/lib/kubelet/kubeconfig --log-dir=/var/log/kubernetes --logtostderr=false --v=2

/opt/kubernetes/bin/kube-proxy --kubeconfig=/var/lib/kubelet/kubeconfig --proxy-mode=iptables --masquerade-all=true --log-dir=/var/log/kubernetes --logtostderr=false --v=2

/opt/kubernetes/bin/kubelet --cloud-provider=vsphere --cloud-config=/etc/cloud.conf --kubeconfig=/var/lib/kubelet/kubeconfig --api-servers=https://k8s-seb.dev.safaribooks.com --cluster-dns=10.100.0.10 --cluster-domain=dev-seb.local --enable-server --pod-manifest-path=/etc/kubernetes/manifests --network-plugin=cni --network-plugin-dir=/etc/cni/net.d --tls-cert-file=/etc/kubernetes/ssl/k8s-seb1.dev.safaribooks.com.crt --tls-private-key-file=/etc/kubernetes/ssl/k8s-seb1.dev.safaribooks.com.key --resolv-conf= --allow-privileged=true --log-dir=/var/log/kubernetes --logtostderr=false --v=2

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
