## Secrets backups / restore via LastPass

If you haven't populated the secrets, the `make` command will prompt you for them.

Then you can write them to vault, and back them up to lastpass
```
make vault_restore_secrets_from_lastpass
make PUSH_LASTPASS=true vault_backup_secrets_to_lastpass
```

the `make` command will exit if secrets aren't pre-loaded into Vault, and guide you with the commands to set all needed secrets.

lastpass_to_vault target expects a Folder in LastPass named 'k8s-landscaper'
with LastPass "Notes" named the git branch (e.g., "master").

TODO: LastPass needs to be cleaned out for unused secrets to avoid cruft
