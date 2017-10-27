from .cluster import Cluster
from .vault import VaultClient
from .cluster_minikube import MinikubeCluster
from .cluster_terraform import TerraformCluster
from .cluster_unmanaged import UnmanagedCluster

class ClusterCollection(object):
    def __init__(self, cloud_collection, charts_git_branch_selector):
        self.vault_cluster_prefix = '/secret/landscape/clusters'
        self.charts_git_branch_selector = charts_git_branch_selector
        self.__clouds = cloud_collection
        self.__vault = VaultClient()
        self.__clusters = self.__clusters_in_vault()



    def __str__(self):
        return str(self.__clusters)


    def __getitem__(self, cluster_name):
        return self.__clusters[cluster_name]

    def __clusters_in_vault(self):
        """ Only retrieve clusters referencing a cloud in self.__clouds"""
        clusters_in_vault = self.__vault.dump_vault_from_prefix(self.vault_cluster_prefix, strip_root_key=True)
        cluster_db = {}
        for k8s_context_name in clusters_in_vault.keys():
            if not self.charts_git_branch_selector or self.charts_branch_subscription_for_cluster(k8s_context_name) == self.charts_git_branch_selector:
                cluster_candidate = clusters_in_vault[k8s_context_name]
                cluster_parameters = clusters_in_vault[k8s_context_name]
                cluster_parameters.update({'context_id': k8s_context_name})
                cloud_id_for_cluster = cluster_candidate['cloud_id']

                if cluster_candidate['cloud_id'] in self.__clouds.list():
                    # What provisioned the cloud? e.g., terraform, minikube
                    cloud_for_cluster = self.__clouds[cloud_id_for_cluster]

                    cloud_provisioner = cloud_for_cluster['provisioner']
                    if cloud_provisioner == 'minikube':
                        cluster_db[k8s_context_name] = MinikubeCluster(**cluster_parameters)
                    elif cloud_provisioner == 'terraform':
                        # pass google credentials to terraform
                        cluster_parameters.update({'google_credentials': cloud_for_cluster.gce_creds })
                        cluster_db[k8s_context_name] = TerraformCluster(**cluster_parameters)
                    elif cloud_id_for_cluster == 'unmanaged':
                        cluster_db[k8s_context_name] = UnmanagedCluster(**cluster_parameters)
                    else:
                        raise("Unknown provisioner found in Vault: {0}".format())
        return cluster_db

    def charts_branch_subscription_for_cluster(self, cluster_name):
        """
        Given a cluster name, return the git branch it watches for chart deploys
        """
        vault_cluster_prefix = '/secret/landscape/clusters'
        vault_path = self.vault_cluster_prefix + '/' + cluster_name
        return self.__vault.get_vault_data(vault_path)['landscaper_branch']


    def list(self):
        return self.__clusters
