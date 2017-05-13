### Secrets naming convention
The format of a secret name includes the chart name so as to namespace it and avoid overriding the root user's environment variables (for security)

# Secrets usage

Secrets are generally passed to chart templates in one of two ways: using secretKeyRef or volume mounts in a k8s definition yaml file. These are the preferred methods - however they don't support combining configurations (stored in git and can be viewed by anyone) with secrets (stored in Vault). Here is an example of a case where you can't use these methods:
```
psql://${database_user}:${database_password}@${database_host}/${database_name}
```

It doesn't make sense to put that whole string inside of a secret. There are two bits of protected information (`database_password` and `database_host`) that need to go into Vault - otherwise leave configurations in git so users without Vault privileges can see how things are configured.

# init-setup init-container
Pods that need to use advanced templating (to generate the above psql:// connection string, for example), we use init containers (and by convention call this templating operation 'init-setup')

The psql:// connection string above can be specified in the Helm chart default values as:

```values.yaml
database_user: myusername
database_name: mydbname
database_password: <not entered here! configure in Vault!>
database_host: <not entered here! configure in Vault!>
```

landscaper will use its `secrets:` definition to populate the secrets, upon deploy

## Secrets
Secrets are pulled from Vault via [envconsul](envconsul.io) via `landscaper apply`.
Environment variables pulled from Vault are prefixed with the string "SECRET_".
This is to prevent overriding root user environment variables, for security reasons.
Landscape `secrets` must use a 'secret-' prefix in their names.

