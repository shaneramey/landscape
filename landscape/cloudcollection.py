from .vault import VaultClient
from .cloud_minikube import MinikubeCloud
from .cloud_terraform import TerraformCloud

class CloudCollection(object):
    def __init__(self, cloud_provisioner, tf_root):
        self.__provisioner = cloud_provisioner
        self.tf_root = tf_root
        self.__vault = VaultClient()
        self.__clouds = self.__clouds_in_vault()


    def __str__(self):
        return '\n'.join(self.__clouds)


    def __getitem__(self, cloud_name):
        retval = self.__clouds[cloud_name]
        return retval

    def __clouds_in_vault(self):
        vault_cloud_prefix = '/secret/landscape/clouds'
        clouds_in_vault = self.__vault.dump_vault_from_prefix(vault_cloud_prefix, strip_root_key=True)
        cloud_db = {}
        for cloud_id in clouds_in_vault.keys():
            cloud_parameters = clouds_in_vault[cloud_id]
            cloud_in_vault_provisioner = cloud_parameters['provisioner']
            if cloud_in_vault_provisioner == self.__provisioner or self.__provisioner is None:
                cloud_parameters.update({'name': cloud_id})
                if cloud_in_vault_provisioner == 'minikube':
                    cloud_db[cloud_id] = MinikubeCloud(**cloud_parameters)
                elif cloud_in_vault_provisioner == 'terraform':
                    cloud_parameters.update({'terraform_templates_dir': self.tf_root})
                    cloud_db[cloud_id] = TerraformCloud(**cloud_parameters)
                else:
                    raise("Unknown provisioner found in Vault: {0}".format())
        return cloud_db


    def list(self):
        return self.__clouds