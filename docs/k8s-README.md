# Landscape

Notes: one app setup (landscaper) using remote
```
git clone https://github.com/Eneco/landscaper.git
cd landscaper
git checkout 1.0.0
```

Goals:
- Mirror any deployed Kubernetes environment (to a local or other remote environment)
- Teach about Kubernetes
  Concepts Demonstrated:
    - Site Reliability Engineering (SRE)
      - Define SLI monitoring and SLO thresholds
        - Graphing (Trending)
        - Alerting
      - Deployment Pipeline

      - Monitoring
    - SLO- PersistentVolumes to define persistent disks (disk lifecycle not tied to the Pods).
    - Services to enable Pods to locate one another.
    - External Load Balancers to expose Services externally.
    - Deployments to ensure Pods stay up and running.
    - Secrets to store sensitive passwords.


To install a full Kubernetes landscape to be used for

Composed of:
- Apps
  - KubeDNS (Provides DNS and Service Discovery)
  - (Optional) Kubernetes-Dashboard
  - (Optional) [NewRelic](https://github.com/kubernetes/kubernetes/tree/release-1.5/examples/newrelic)
  - (Optional) Sample Apps
- Default resource limits
- TLS PKI infrastructure (client, user and server certs)
- User authentication

## Developer Setup

- (MacOS) Install [Kube Solo](https://github.com/TheNewNormal/kube-solo-osx)

- [Install Helm into Kube Solo](https://github.com/TheNewNormal/kube-solo-osx)
```
install_deis
```

## Cloud Provider Setup

- Kubeadm
```
kubeadm init --kubernetes-version v1.6.1 --service-dns-domain downup.local
label the kubernetes master with `kubeadm.alpha.kubernetes.io/role: master`

# Enable the master to run pods
kubectl taint nodes --all node-role.kubernetes.io/master-

# Install CNI network plugin (Canal is a policy controller for Calico (BGP) + Flannel (VXLAN)
kubectl apply -f https://raw.githubusercontent.com/projectcalico/canal/master/k8s-install/kubeadm/1.6/canal.yaml

# Install Helm

# Set up Helm ServiceAccount
https://github.com/kubernetes/helm/issues/2224
kubectl create serviceaccount --namespace kube-system tiller
kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
kubectl edit deploy --namespace kube-system tiller-deploy #and add the line serviceAccount: tiller to spec/template/spec


```

- Install Kubernetes-Anywhere


## Helm convention guidelines
https://gist.github.com/so0k/f927a4b60003cedd101a0911757c605a

## Other resources
https://github.com/kubernetes/helm/blob/master/docs/related.md

