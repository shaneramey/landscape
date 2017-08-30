class Chart(object):
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
        self.configuration = kwargs['configuration']
        self.secrets = kwargs['secrets']

