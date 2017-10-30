from .cluster_minikube import MinikubeCluster
from .cluster_terraform import TerraformCluster
from .cluster_unmanaged import UnmanagedCluster
from .vault import VaultClient


class ClusterCollection(object):
    """A group of clusters.

    Generates a list of clusters. Cluster type is determined by its Cloud's
    "provisioner" attribute. Each cluster behaves differently (i.e., which
    chart directories to deploy, what the converge steps are) based on its type

    Attributes:
        None.
    """

    def __init__(self, cloud_collection, charts_git_branch_selector):
        """initializes a ClusterCollection for a given git branch.

        Reads a dict of clusters from Vault, and filter the results based on the
        git branch passed into the constructor.

        Args:
            cloud_collection(List): Clouds that contain the cluster(s). Used to
                identify the cluster's type
            charts_git_branch_selector(str): If set, ClusterCollection is
                composed of only clusters subscribed to this branch. Set in
                Vault-defined settings for the cluster

        Returns:
            None.

        Raises:
            None.
        """

        self.vault_cluster_prefix = '/secret/landscape/clusters'
        self.charts_git_branch_selector = charts_git_branch_selector
        self.__clouds = cloud_collection
        self.__vault = VaultClient()
        self.__clusters = self.__clusters_in_vault()

    def __str__(self):
        """Pretty-prints a list of clusters

        Args:
            self: the current object

        Returns:
            A new-line separated str of cluster names

        Raises:
            None.
        """

        return '\n'.join(self.__clusters.keys())


    def __getitem__(self, cluster_name):
        """returns a Cluster with a given name

        Args:
            cluster_name: index for the cluster within self.__clusters

        Returns:
            A single Cluster object named cluster_name.

        Raises:
            None.
        """
        return self.__clusters[cluster_name]

    def __clusters_in_vault(self):
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

        # Dump Vault
        clusters_in_vault = self.__vault.dump_vault_from_prefix(
            self.vault_cluster_prefix, strip_root_key=True)
        cluster_db = {}
        # Look at each Vault key's name for its context
        for k8s_context_name in clusters_in_vault.keys():
            # If charts_git_branch_selector is None, generate collection of
            # all clusters. Otherwise, generate collection including only
            # clusters subscribing to this branch.
            if not self.charts_git_branch_selector or \
                self.charts_gitbranch_for_cluster(k8s_context_name) \
                == self.charts_git_branch_selector:

                # find cluster's cloud name and determine cloud's provisioner
                cluster_parameters = clusters_in_vault[k8s_context_name]
                cluster_parameters.update({'context_id': k8s_context_name})
                cloud_id_for_cluster = cluster_parameters['cloud_id']

                if cluster_parameters['cloud_id'] in self.__clouds.list():
                    # What provisioned the cloud? e.g., terraform, minikube
                    cloud_for_cluster = self.__clouds[cloud_id_for_cluster]
                    cloud_provisioner = cloud_for_cluster['provisioner']

                    # Load specific cluster type based on cloud provisioner
                    if cloud_provisioner == 'minikube':
                        cluster_db[k8s_context_name] = MinikubeCluster(
                            **cluster_parameters)
                    elif cloud_provisioner == 'terraform':
                        # pass google credentials to terraform
                        cluster_parameters.update(
                            {'google_credentials': cloud_for_cluster.gce_creds})
                        cluster_db[k8s_context_name] = TerraformCluster(
                            **cluster_parameters)
                    elif cloud_id_for_cluster == 'unmanaged':
                        cluster_db[k8s_context_name] = UnmanagedCluster(
                            **cluster_parameters)
                    else:
                        raise(
                            "Unknown cloud provisioner in Vault: {0}".format())
        return cluster_db

    def charts_gitbranch_for_cluster(self, cluster_name):
        """Link a Kubernetes cluster with a landscaper git branch.

        Each Kubernetes cluster subscribes to a single git branch for its
        helm chart secrets. Retrieve that subscription from Vault.

        Args:
            cluster_name: The name of the Kubernetes cluster/context in Vault.

        Returns:
            A string with the git branch name (of the landscape repo) to apply
            to the cluster.

        Raises:
            None.
        """

        vault_cluster_prefix = '/secret/landscape/clusters'
        vault_path = self.vault_cluster_prefix + '/' + cluster_name
        return self.__vault.get_vault_data(vault_path)['landscaper_branch']

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
