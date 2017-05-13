# Prerequisites

# Vault

Generate a minikube k8s/landscape/helm/vault environment:
```
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
export VAULT_ADDR=http://127.0.0.1:8200
vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | tail -n 1 | awk -F ': ' '{ print $2 }'`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
```
If you haven't populated the secrets, the `make` command will prompt you

### Landscaper
```
wget https://github.com/Eneco/landscaper/releases/download/1.0.1/landscaper-v1.0.1-linux-amd64
sudo mv landscaper-v1.0.1-linux-amd64 /usr/local/bin/landscaper
```

### Envconsul
wget https://releases.hashicorp.com/envconsul/0.6.2/envconsul_0.6.2_darwin_amd64.tgz
tar zxvf envconsul_0.6.2_darwin_amd64.tgz
sudo mv envconsul /usr/local/bin/

### Helm

Add the helm chart repo
```
helm repo add charts.downup.us http://charts.downup.us
```
