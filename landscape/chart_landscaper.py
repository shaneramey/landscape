class LandscaperChart(object):
    """Kubernetes Helm Chart deployment information

    Represents a Chart to be deployed. Includes configuration overrides
    and secrets list

    Args:
        **kwargs (dict): Arguments representing Chart attribute parameters

    Attributes:
        name (str): Human readable string describing the exception.
        namespace (str): Human readable string describing the exception.
        release (dict): Chart and version k/v pairs
        configuration (dict): Configuration overrides for Chart values
        secrets (list): Secrets to be pulled from Vault
	"""
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.namespace = kwargs['namespace']
        self.release = kwargs['release']
        self.filepath = kwargs['filepath']

        # configuration and secrets are optional fields in landscaper yaml
        self.configuration = {}
        self.secrets = []
        if 'configuration' in kwargs:
            self.configuration = kwargs['configuration']
        if 'secrets' in kwargs:
            self.secrets = kwargs['secrets']

    def __str__(self):
        """Pretty-prints a chart deployment

        Args:
            self: the current object

        Returns:
            A new-line separated str of charts in format:
            namespace/chart_name

        Raises:
            None.
        """
        return "{0}/{1}".format(self.namespace, self.name)


