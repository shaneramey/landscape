class Cloud(object):
    """
    vault write /secret/landscape/clouds/staging-165617 provisioner=terraform
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.provisioner = kwargs['provisioner']


    def __getitem__(self, x):
        return getattr(self, x)


    def __str__(self):
        return self.name

    def converge(self):
        """
        Override this method in your subclass
        """
        raise NotImplementedError()

