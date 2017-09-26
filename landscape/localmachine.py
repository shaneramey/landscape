import platform
from .kubernetes import kubectl_use_context
from .helm import apply_tiller

class Localmachine(object):
    """
    Converges local machine for one cluster at a time
    Does:
     - import CA cert (the same CA cert that TLS-enabled pods import)
     - adds helm repo that's authoritative in cluster
       (the same repo used by Jenkins for helm charts)
     - downloads + imports OpenVPN profile to local machine
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    """

    def __init__(self, **kwargs):
        self.os_platform = platform.system()
        self.vm_clouds  = kwargs['cloud_collection']
        self.kubernetes_clusters = kwargs['cluster_collection']


    def converge(self):
        """
        Override this method in your subclass
        """
        print('TODO: (minikube) import CA') # cluster
        print('sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.minikube/ca.crt')
        print('TODO: helm add repos (pulled from where? Vault?)') # cluster
        print('TODO: Download OpenVPN profile') # cluster
        print("vm_clouds={0}".format(self.vm_clouds))
        print("kubernetes_clusters={0}".format(self.kubernetes_clusters))
