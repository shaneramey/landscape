# Goals

Put Kubernetes stack in any environment, with any of the following parameters
 - Any DNS domain (so devs can uniquely identify their stacks)
 - Any network range (so networks can be universally connected)
 - any PKI infrastructure, so a stack can be signed by/trusted with a single CA
 - privileged vs non-privileged containers should work as a toggle in any stack

# How parameters are passed
Cluster creation
 - minikube
```
  minikube start --kubernetes-version=v1.6.0 \
    --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
    --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
    --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
    --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
    --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
    --extra-config=apiserver.GenericServerRunOptions.AuthorizationMode=RBAC \
    --cpus=4 \
    --disk-size=20g \
    --memory=4096
```
 - kops (GCE, AWS)

## Parameters to Kubernetes components

List to understand what we're using

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
