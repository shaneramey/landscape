from .cluster import Cluster
from .vault import VaultClient
from .cluster_minikube import MinikubeCluster
from .cluster_terraform import TerraformCluster

class ClusterCollection(object):
    def __init__(self, cloud_collection):
        self.__clouds = cloud_collection
        self.__vault = VaultClient()
        self.__clusters = self.__clusters_in_vault()


    def __str__(self):
        return str(self.__clusters)


    def __getitem__(self, cluster_name):
        return self.__clusters[cluster_name]

    def __clusters_in_vault(self):
        """ Only retrieve clusters referencing a cloud in self.__clouds"""
        vault_cluster_prefix = '/secret/landscape/clusters'
        clusters_in_vault = self.__vault.dump_vault_from_prefix(vault_cluster_prefix, strip_root_key=True)
        cluster_db = {}
        for k8s_context_name in clusters_in_vault.keys():
            cluster_candidate = clusters_in_vault[k8s_context_name]
            cloud_id_for_cluster = cluster_candidate['cloud_id']
            if cluster_candidate['cloud_id'] in self.__clouds.list():
                # What provisioned the cloud? e.g., terraform, minikube
                cloud_for_cluster = self.__clouds[cloud_id_for_cluster]
                cluster_parameters = clusters_in_vault[k8s_context_name]
                cluster_parameters.update({'context_id': k8s_context_name})
                cloud_provisioner = cloud_for_cluster['provisioner']
                if cloud_provisioner == 'minikube':
                    cluster_db[k8s_context_name] = MinikubeCluster(**cluster_parameters)
                elif cloud_provisioner == 'terraform':
                    # pass google credentials to terraform
                    cluster_parameters.update({'google_credentials': cloud_for_cluster.gce_creds })
                    cluster_db[k8s_context_name] = TerraformCluster(**cluster_parameters)
                else:
                    raise("Unknown provisioner found in Vault: {0}".format())
        return cluster_db

    def list(self):
        return self.__clusters
