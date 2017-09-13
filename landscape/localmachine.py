import platform
from .kubernetes import kubectl_use_context
from .prerequisites import install_prerequisites
from .helm import apply_tiller

class Localmachine(object):
    """
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    """

    def __init__(self, **kwargs):
        self.os_platform = platform.system()

    def post_converge(self):
        """
        Override this method in your subclass
        """
        print('TODO: (minikube) import CA')
        print('TODO: helm add repos (pulled from where? Vault?)')
        print('TODO: Download OpenVPN profile')
        print('TODO: export local vault with remote vault')

    def pre_converge(self):
        install_prerequisites(self.os_platform)
