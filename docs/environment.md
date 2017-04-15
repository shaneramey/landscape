# Docker registry

gcloud docker -- login us.gcr.io
docker login -e shane.ramey@gmail.com -u oauth2accesstoken -p "$(gcloud auth print-access-token)" https://us.gcr.io

# Envconsul
Used to read secrets from Hashicorp Vault into environment variables

see [envconsul-vault.md](envconsul-vault.md) for details of a local testing setup

 - run 'AWS_ACCESSKEY=01234abc AWS_SECRETKEY=98765432 AWS_REGION=us-west-2 S3_BUCKET=mybucket landscaper apply --dir landscape/helm-chart-publisher/helm-chart-publisher/ --namespace=helm-chart-publisher'

# Authenticate to Vault (local dev-mode)
vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | awk -F ': ' '{ print $2 }'`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
