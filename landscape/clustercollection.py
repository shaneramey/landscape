from .cloudcollection import CloudCollection
from .cluster import Cluster
from .vault import VaultClient
from .cluster_minikube import MinikubeCluster
from .cluster_terraform import TerraformCluster

class ClusterCollection(object):
    def __init__(self):
        self.__vault = VaultClient()
        self.__clusters = self.__clusters_in_vault()


    def __getitem__(self, cluster_name):
        retval = [d for d in self.__clusters if d['name'] == cluster_name][0]
        return retval

    def __clusters_in_vault(self):
        vault_cluster_prefix = '/secret/landscape/clusters'
        clusters_in_vault = self.__vault.dump_vault_from_prefix(vault_cluster_prefix, strip_root_key=True)
        cluster_db = []
        for cluster_id in clusters_in_vault.keys():
            cluster_parameters = clusters_in_vault[cluster_id]
            cluster_parameters.update({'context_id': cluster_id})
            print("cluster_parameters={0}".format(cluster_parameters))
            cloud_hosting_cluster = cluster_parameters['cloud_id']
            clouds = CloudCollection()
            cloud_provisioner = clouds[cloud_hosting_cluster]['provisioner']
            if cloud_provisioner == 'minikube':
                cluster_db.append(MinikubeCluster(**cluster_parameters))
            elif cloud_provisioner == 'terraform':
                cluster_db.append(TerraformCluster(**cluster_parameters))
            else:
                raise("Unknown provisioner found in Vault: {0}".format())
        return cluster_db

    def list(self, cloud_id_selector=None):
        clusters = self.__clusters
        if cloud_id_selector:
            retval = [d for d in clusters if d['cloud_id'] == cloud_id_selector]
        else:
            retval = clusters
        return retval