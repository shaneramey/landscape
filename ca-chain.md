# CA Certificates

- Root CA
  - Intermediate CA
    - cluster1 CA
    - cluster2 CA
    - cluster3 CA

Landscaper Jenkins job bring up new environment
deploy $BRANCH_NAME to $KUBERNETES_CONTEXT
```
git checkout $BRANCH_NAME
kubeconfig use-context $KUBERNETES_CONTEXT
make deploy
```
