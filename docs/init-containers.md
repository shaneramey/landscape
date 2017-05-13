# init-containers
init-containers are widely used in the Landscape-compatible Helm Charts repo
init-containers are typically used for the following:
- substitute secrets into Helm templates
- generate TLS certificate signing requests (CSRs), and place them on the filesystem
- Other pre-application-container initialization

Example configmap in an init chart:
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: secrets-inject
  labels:
    chart: "{{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}"
data:
  init.sh:
    #! /bin/sh
    sed -e 's/__SECRET_HELLO_NAME__/$SECRET_HELLO_NAME/g' hello-secret.config.tmpl  > /post-secrets/hello-secret.config
    sed -ie 's/__SECRET_HELLO_AGE__/$SECRET_HELLO_AGE/g' /post-secrets/hello-secret.config
  hello-secret.config.tmpl:
    hello:
      age: "__SECRET_HELLO_AGE__"
      name: "__SECRET_HELLO_NAME__"
```

An example init-container looks like this:

```
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  template:
    metadata:
      annotations:
        pod.alpha.kubernetes.io/init-containers: '[
            {
                "name": "subst-config-secrets",
                "image": "busybox:latest",
                "command": ["/secrets-conversion/init.sh"],
                "workingDir": "/initial-certificate-store",
                "volumeMounts": [
                  {
                    "name": "replace-secrets",
                    "mountPath": "/pre-secrets"
                  },
                  {
                    "name": "workdir",
                    "mountPath": "/post-secrets"
                  }
                ]
            }
        ]'
    spec:
      containers:
      - name: myapp
        image: myapp:1.0
        command: ["/bin/myapp", "-c", "/config/hello-secret.config"]
        volumeMounts:
        - name: workdir
          mountPath: /config
      volumes:
        - name: workdir
          emptyDir: {}
        - name: replace-secrets
          configMap:
            name: secrets-inject
            defaultMode: 0755
            items:
            - key: init.sh
              path: init.sh
            - key: hello-secret.config.tmpl
              path: hello-secret.config.tmpl
```