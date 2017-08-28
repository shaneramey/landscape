class Chart(object):

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.namespace = kwargs['namespace']
        self.release = kwargs['release']
        self.configuration = kwargs['configuration']
        self.secrets = kwargs['secrets']

