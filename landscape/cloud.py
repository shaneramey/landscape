class Cloud(object):
    """A single generic cloud provider. Meant to be subclassed. Examples:

    vault write /secret/landscape/clouds/staging-123456 provisioner=terraform
    vault write /secret/landscape/clouds/minikube provisioner=minikube

    Cloud attributes are read from Vault in a CloudCollection class,
    which are loaded into a provisioner-specific subclass

    Attributes:
        name: Name to uniquely identify the cloud.
        provisioner: Tool used to provision the cloud.
    """

    def __init__(self, **kwargs):
        """Initializes a Cluster.

        Reads a cluster's definition from Vault.

        Args:
            kwargs**:
              name: the Cloud's unique name
              provisioner: The tool that provisioned the cloud

        Returns:
            None

        Raises:
            None
        """
        self.name = kwargs['name']
        self.provisioner = kwargs['provisioner']


    def __getitem__(self, x):
        """Enables the Cloud object to be subscriptable.

        Args:
            x: the element being subscripted.

        Returns:
            An arbitrary attribute of the class.

        Raises:
            None.
        """
        return getattr(self, x)


    def __str__(self):
        """Returns the cloud's name.

        Args:
            None.

        Returns:
            A String containing the cloud's unique name.

        Raises:
            None.
        """
        return self.name


    def converge(self):
        """Override this method in your subclass.

        Args:
            None.

        Returns:
            None.

        Raises:
            NotImplementedError if called directly.
        """
        raise NotImplementedError()
