import hvac
from .vault import VaultClient

class CloudCollection(object):
    def __init__(self):
        self.__vault = VaultClient()
        self.__clouds = self.__clouds_in_vault()


    def __clouds_in_vault(self):
        vault_cloud_prefix = '/secret/landscape/clouds'
        clouds_in_vault = self.__vault.dump_vault_from_prefix(vault_cloud_prefix, strip_root_key=True)
        cloud_db = []
        for cloud in clouds_in_vault.keys():
            print("cloud={0}".format(cloud))
            cloud_parameters = clouds_in_vault[cloud]
            cloud_parameters_with_name = cloud_parameters.update({'name': cloud})
            cloud_db.append(Cloud(**cloud_parameters))
        print("cloud_db={0}".format(cloud_db))
        return cloud_db


    def list(self, cloud_type=None):
        clouds = self.__clouds
        if cloud_type:
            retval = [d for d in clouds if d['provisioner'] == cloud_type]
        else:
            retval = clouds
        return retval


class Cloud(object):
    """
    vault write /secret/landscape/clouds/staging-165617 provisioner=terraform
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """
    def __init__(self, **kwargs):
        self.provisioner = kwargs['provisioner']
        self.name = kwargs['name']
        print("prov={0}".format(kwargs['provisioner']))
        print("name={0}".format(kwargs['name']))

    def __getitem__(self, x):
        return getattr(self, x)
