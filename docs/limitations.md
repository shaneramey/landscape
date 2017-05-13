Limitations:
- Chart names can only be deployed once per namespace
   to conform to the structure of vault and landscaper
   Example: there must only be one `nginx` chart in namespace `myapp`
- Each cluster gets its own cluster domain (in /etc/resolv.conf on each pod and external calls to services). FIXME: explain this
