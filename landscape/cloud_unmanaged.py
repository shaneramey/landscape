import subprocess
import sys
import logging

from .cloud import Cloud

class UnmanagedCloud(Cloud):
    """
    Represents a Cloud provisioned outside of this tool
    """
    def __init__(self, **kwargs):
        Cloud.__init__(self, **kwargs)

    def converge(self):
        """
        For an UnmanagedCloud, don't converge anything
        """
        return True
