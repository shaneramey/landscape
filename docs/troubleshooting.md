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
