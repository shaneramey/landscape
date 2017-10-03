import subprocess
import logging

from .cluster import Cluster

class MinikubeCluster(Cluster):
    """
    Represents a Cluster provisioned in minikube

    Secrets path must exist as:
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """
    pass

    def cluster_setup(self):
        """
        Checks if a minikube cloud is already running
        Initializes it if not yet running
        """
        logging.info('Configuring minikube addons')
        disable_addons = ['kube-dns', 'registry-creds', 'ingress']
        enable_addons = ['default-storageclass']
        for disable_addon in disable_addons:
            addon_cmd = "minikube addons disable {0}".format(disable_addon)
            check_cmd_failed = subprocess.call(addon_cmd, shell=True)
            if check_cmd_failed:
                logging.warn("Failed to disable addon with command: {0}".format(addon_cmd))

        for enable_addon in enable_addons:
            addon_cmd = "minikube addons enable {0}".format(enable_addon)
            check_cmd_failed = subprocess.call(addon_cmd, shell=True)
            if check_cmd_failed:
                logging.warn("Failed to enable addon with command: {0}".format(addon_cmd))

    def configure_kubectl(self):
        """
        Do nothing
        """
        logging.info("Using minikube's pre-configured KUBECONFIG entry")

