from .cluster_minikube import MinikubeCluster
from .cluster_terraform import TerraformCluster
from .cluster_unmanaged import UnmanagedCluster
from .vault import VaultClient

from .cloudcollection import CloudCollection # for linking a cluster to a cloud


class ClusterCollection(object):
    """A group of clusters.

    Generates a list of clusters. Cluster type is determined by its Cloud's
    "provisioner" attribute. Each cluster behaves differently (i.e., which
    chart directories to deploy, what the converge steps are) based on its type

    Attributes:
        clusters: (optionally) filtered list of clusters, read from Vault
    """

    def __init__(self, cloud_collection, cloud_selector, charts_git_branch_selector):
        """initializes a ClusterCollection for a given git branch.

        Reads a dict of clusters from Vault, and filter the results based on the
        git branch passed into the constructor.

        Args:
            cloud_collection(List): Clouds that contain the cluster(s). Used to
                identify the cluster's type
            cloud_selector(str): If set, ClusterCollection is composed of only
                clusters in this cloud
            charts_git_branch_selector(str): If set, ClusterCollection is
                composed of only clusters subscribed to this branch. Set in
                Vault-defined settings for the cluster

        Returns:
            None.

        Raises:
            None.
        """

        self.charts_git_branch_selector = charts_git_branch_selector
        self.cloud_selector = cloud_selector
        self.__clouds = cloud_collection
        self.clusters = self.__filter_clusters(cloud_selector, charts_git_branch_selector)

    def __str__(self):
        """Pretty-prints a list of clusters

        Args:
            self: the current object

        Returns:
            A new-line separated str of cluster names

        Raises:
            None.
        """
        cluster_names = []
        for cluster in self.clusters:
            cluster_names.append(cluster.name)
        return '\n'.join(cluster_names)


    def __getitem__(self, cluster_name):
        """returns a Cluster with a given name

        Args:
            cluster_name: index for the cluster within self.clusters

        Returns:
            A single Cluster object named cluster_name.

        Raises:
            None.
        """
        cluster = next((item for item in self.clusters if item.name == cluster_name))
        return cluster

    def __filter_clusters(self, cloud_selection, charts_branch_selection):
        """Loads clusters from Vault and filters them
        """
        vault_clusters = self.__load_clusters_from_vault()
        filtered_clusters = []
        # Look at each Vault key's name for its context
        for vault_cluster in vault_clusters:
            # If charts_git_branch_selector is None, generate collection of
            # all clusters. Otherwise, generate collection including only
            # clusters subscribing to this branch.
            if charts_branch_selection == vault_cluster.landscaper_branch or \
                not charts_branch_selection:
                if cloud_selection == vault_cluster.cloud_id or \
                    not cloud_selection:
                    filtered_clusters.append(vault_cluster)

        return filtered_clusters


    def __load_clusters_from_vault(self):
        """Retrieves cluster definitions from Vault and loads them into a dict

        Recurses through Vault looking to only retrieve clusters referencing a
        cloud in self.__clouds

        Args:
            None.

        Returns:
            A dict mapping keys to the corresponding table row data
            fetched. Each row is represented as a tuple of strings. For
            example:

            {
                'gke_staging-123456_us-west1-a_master': <TerraformCluster>,
                'minikube': <MinikubeCluster>
            }

        Raises:
            None.
        """
        vault_cluster_prefix = '/secret/landscape/clusters'
        # Dump Vault
        cluster_defs = VaultClient().dump_vault_from_prefix(
            vault_cluster_prefix, strip_root_key=True)
        clouds = CloudCollection()
        clusters = []
        for cluster_name in cluster_defs:
            # inject cluster name into data
            cluster_def = cluster_defs[cluster_name]
            cluster_def.update({'context_id': cluster_name})
            cloud_name_for_cluster = cluster_def['cloud_id']
            cloud_for_cluster = clouds[cloud_name_for_cluster]
            cloud_provisioner = cloud_for_cluster.provisioner

            # Load specific cluster type based on cloud provisioner
            if cloud_provisioner == 'minikube':
                clusters.append(MinikubeCluster(**cluster_def))
            elif cloud_provisioner == 'terraform':
                cluster_def.update(
                            {'google_credentials': cloud_for_cluster.gce_creds})
                clusters.append(TerraformCluster(**cluster_def))
            elif cloud_provisioner == 'unmanaged':
                clusters.append(UnmanagedCluster(**cluster_def))
            else:
                raise("Unknown cloud provisioner: {0}".format(cloud_provisioner))
        return clusters


    def list(self):
        """Generates list of clusters and returns them.

        Args:
            None

        Returns:
            a dict of clusters that may have been filtered from a larger dict.
            For example:

            {
                'gke_staging-123456-west1-a_master': <TerraformCluster>,
                'minikube': <MinikubeCluster>
            }


        Raises:
            None.
        """

        return self.__clusters
