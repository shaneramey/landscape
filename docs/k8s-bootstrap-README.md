# k8s bootstrap

Installs the following applications:
 - KubeDNS (Provides DNS and Service Discovery)
 - Kubernetes-Dashboard (TODO: Optional)
 - Heapster (TODO: Optional)
 TODO:
 - (Optional) [NewRelic](https://github.com/kubernetes/kubernetes/tree/release-1.5/examples/newrelic)
 - Add-on applications via Helm/Landscaper
    - applications are expected to utilize Kubernetes CertificateSigningRequest objects to generate their TLS certs (https://github.com/kubernetes/kubernetes.github.io/pull/2939/files)
    - Gatekeepers of each environment must sign certificates via `kubectl certificate (approve|deny)` (an automated process is on the k8s roadmap to be automated by a deployed controller pod)

## Kube-Solo (MacOS)
Setup Instructions:
 - Install [Kube-Solo](https://github.com/TheNewNormal/kube-solo-osx)
 - Install Helm via Kube-Solo menu option

## Kubernetes-Anywhere
Supports:
 - GCE
 - vSphere
 - Others as specified in the Kubernetes-Anywhere repo

## Tests
Helm has a testing facility. 
Place a -tests.yaml file in your Chart's templates/ directory, such as:
```
apiVersion: v1
kind: Pod
metadata:
  name: "{{.Release.Name}}-credentials-test"
  annotations:
    "helm.sh/hook": test-success
spec:
  containers:
    - name: {{.Release.Name}}-credentials-test
      image: bitnami/mariadb:{{.Values.imageTag}}
      command: ["mysql",  "--host={{.Release.Name}}-mariadb", "--user={{.Values.mariadbUser}}", "--password={{.Values.mariadbPassword}}"]
  restartPolicy: Never
```
you can nest your own test suite inside templates/mytestsuite/tests/ directory

To test, run:
`helm install chartname --name=chartname-test`
`helm test chartname-test

[More info on Helm Tests](https://github.com/kubernetes/helm/blob/master/docs/chart_tests.md)