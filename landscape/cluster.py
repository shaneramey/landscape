from .kubernetes import kubectl_use_context
from .helm import apply_tiller

class Cluster(object):
    """A single generic Kubernetes cluster. Meant to be subclassed.

    Should include methods to initialize a kubernetes cluster and install helm.

    Attributes:
        name: the name of the cluster
        cloud_id: the cloud that provisioned the cluster's ID

    """
    def __init__(self, **kwargs):
        """initializes a Cluster.

        Reads a cluster's definition from Vault.

        Args:
            kwargs**:
              context_id: the Cluster's context name on local machine
              cloud_id: a list of Clouds, one of which should (if defined
              in Vault properly) host the Cluster

        Returns:
            None

        Raises:
            None
        """

        self.name = kwargs['context_id']
        self.cloud_id = kwargs['cloud_id']


    def __getitem__(self, x):
        return getattr(self, x)


    def __str__(self):
        return self.name


    def converge(self):
        """
        Override these methods in your subclass
        """
        self.cluster_setup()
        self._configure_kubectl_credentials()
        apply_tiller(self.name)


    def cluster_setup(self):
        raise NotImplementedError('Must be overridden in subclass')


    def _configure_kubectl_credentials(self):
        raise NotImplementedError('Must be overridden in subclass')
