class Cluster(object):
    """
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    """

    def __init__(self, **kwargs):
        print("kwargs={0}".format(kwargs))
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
        raise NotImplementedError()

