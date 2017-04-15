# Developer envconsul-vault setup

Steps to use:
 - run Vault locally:
```
docker run --cap-add=IPC_LOCK -p 8200:8200 -d --name=dev-vault vault
```
 - Install envconsul
 - Set envconsul configuration (config.hcl) to use your local "dev-vault" container:
```
vault {
  address = "http://127.0.0.1:8200"
  renew  = false
}

secret {
  no_prefix = true
  path   = "/secret/passwords"
  format = "SECRET_{{ key }}"

}
```

 - authenticate to Vault
    see [environment.md](environment.md)

 - run envconsul:
```
vault write secret/passwords username=foo password=bar
envconsul -config="./config.hcl" -secret="secret/passwords" -upcase env
```

## Additional information
[envconsul repo README.md](https://github.com/hashicorp/envconsul/blob/master/README.md)