import subprocess

from .cluster import Cluster

class MinikubeCluster(Cluster):
    """
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """
    pass

    def cluster_setup(self):
        """
        Checks if a minikube cloud is already running
        Initializes it if not yet running

        Returns:

        """
        print('- Configuring minikube addons')
        disable_addons = ['kube-dns', 'registry-creds', 'ingress']
        enable_addons = ['default-storageclass']
        for disable_addon in disable_addons:
            addon_cmd = "minikube addons disable {0}".format(disable_addon)
            check_cmd_failed = subprocess.call(addon_cmd, shell=True)
            if check_cmd_failed:
                print("ERROR: failed to run command".format(addon_cmd))

        for enable_addon in enable_addons:
            addon_cmd = "minikube addons enable {0}".format(enable_addon)
            check_cmd_failed = subprocess.call(addon_cmd, shell=True)
            if check_cmd_failed:
                print("ERROR: failed to run command".format(addon_cmd))

    def configure_kubectl(self):
        print("Using minikube's pre-configured KUBECONFIG entry")

