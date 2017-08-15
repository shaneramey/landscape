class LandscapeVault(object):
    """Manages Vault secrets
    Arguments:

    Methods:
    """
    
    vault_root = '/secret/'
    
    def __init__(self, vault_addr, secret_root):
        self.provisioner = provisioner
        self.gce_project_id = gce_project_id
        self.landscaper_branch = landscaper_branch
        print("LandscapeCluster placeholder")

    @property
    def vault_creds():
        return 
        {
            'VAULT_ADDR': '',
            'VAULT_CACERT': '',
            'VAULT_TOKEN': '',
        }
    def branch():
        return "git branch"
    
    def vault_path_for_deployment(vault_ns, vault_):
        def vault_path = '/secret/landscape/{0}/{1}/{2}'


        vault_path.format(self.branch,
                            self.namespace,
                            self.helm_chart_name
                           )

        return v_path
