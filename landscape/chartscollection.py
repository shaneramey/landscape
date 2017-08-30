import os
import yaml

class ChartsCollection(object):
    """Represents a set of Charts which are loaded up from the deploy
    driver (Currently landscaper, but may support to terraform-provider-helm)

	Should be used as a superclass, subclassed by provisioner-specific objects

    Args:
        None

    Attributes:
        chart_sets (dict): Set of Chart deployment definitions.
	"""
    def list(self):
        """Lists charts"""
        return self.chart_sets
