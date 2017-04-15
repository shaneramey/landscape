# Minikube local installation

OSX
```
curl -Lo minikube https://storage.googleapis.com/minikube/releases/v0.17.1/minikube-darwin-amd64 && chmod +x minikube && sudo mv minikube /usr/local/bin/
```

Running minikube
```
minikube start
eval $(minikube docker-env) # make your local "docker ps" be the one inside k8s
--enable-hostpath-provisioner[=false] on controller-manager
```
