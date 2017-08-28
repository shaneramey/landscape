from .kubernetes import kubectl_use_context
from .helm import apply_tiller

class Cluster(object):
    """
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    """

    def __init__(self, **kwargs):
        self.name = kwargs['context_id']
        self.cloud_id = kwargs['cloud_id']


    def __getitem__(self, x):
        return getattr(self, x)


    def __str__(self):
        return self.name

    def converge(self):
        """
        Override this method in your subclass
        """
        self.cluster_setup()
        self.configure_kubectl()
        self.switch_to_cluster_context()
        apply_tiller()


    def cluster_setup(self):
        raise NotImplementedError('Must be overridden in subclass')

    def configure_kubectl(self):
        raise NotImplementedError('Must be overridden in subclass')

    def switch_to_cluster_context():
        kubectl_use_context(self.name)