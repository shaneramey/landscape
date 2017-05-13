# TLS certificate auto-signing
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


# Auto signing certificate requests
Get list of pending certificates
```
kubectl get csr | grep -v NAME  | awk '{ print $1 }' | grep Pending 
```
