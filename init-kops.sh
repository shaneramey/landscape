
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
  - allow-privileged

Other considerations
- kubernetes federation
#! /usr/bin/env bash
#
# initializes a the following pki certs:
# - root CA ("ca.[crt, key]" - key gets put in LastPass; not stored in Vault)
# - intermediate CA used to sign everything ("intermediate.[crt, key]")
# - cluster intermediate CA cert ("cluster.[crt, key]")
#    - signed by cluster.crt:
#       etcd server ("etcd-server.[crt,key]")
#       etcd client ("etcd-client.[crt,key]")
#       pod client ("pod-client.key" CN=pod-client)
# - client signed by cluster.crt ("pod-client.key")
# - client certificate to talk to etcd ("etcd-client.[crt, key]")
# - k8s components tls arguments
#    - apiserver
#       - tls-cert-file: for https://kubernetes.default.svc/, etc.
#       - tls-private-key-file: for https://kubernetes.default.svc/, etc.
#       - ca-client-file: /var/run/secrets/kubernetes.io/ca.crt on pods
#       - ca cert chain to be placed in
#       - etcd-certfile: client cert for k8s api
#       - etcd-keyfile: client key for k8s api
#       - etcd-cafile: ca cert to auth etcd server
#       - service-account-key-file=pod-client.key
#       - authorization-rbac-super-user=pod-client
#    - controller-manager
#       - root-ca-file ("cluster.crt")
#       - service-account-key-file=pod-client.key
#       - kubeconfig
#    - scheduler
#       - kubeconfig
#    - kube-proxy
#       - kubeconfig