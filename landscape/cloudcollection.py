from .vault import VaultClient
from .cloud_minikube import MinikubeCloud
from .cloud_terraform import TerraformCloud

class CloudCollection(object):
    def __init__(self):
        self.__vault = VaultClient()
        self.__clouds = self.__clouds_in_vault()


    def __getitem__(self, cloud_name):
        retval = [d for d in self.__clouds if d['name'] == cloud_name][0]
        return retval

    def __clouds_in_vault(self):
        vault_cloud_prefix = '/secret/landscape/clouds'
        clouds_in_vault = self.__vault.dump_vault_from_prefix(vault_cloud_prefix, strip_root_key=True)
        cloud_db = []
        for cloud_id in clouds_in_vault.keys():
            cloud_parameters = clouds_in_vault[cloud_id]
            cloud_parameters.update({'name': cloud_id})
            cloud_provisioner = cloud_parameters['provisioner']
            if cloud_provisioner == 'minikube':
                cloud_db.append(MinikubeCloud(**cloud_parameters))
            elif cloud_provisioner == 'terraform':
                cloud_db.append(TerraformCloud(**cloud_parameters))
            else:
                raise("Unknown provisioner found in Vault: {0}".format())
        return cloud_db


    def list(self, cloud_type=None):
        clouds = self.__clouds
        if cloud_type:
            retval = [d for d in clouds if d['provisioner'] == cloud_type]
        else:
            retval = clouds
        return retval