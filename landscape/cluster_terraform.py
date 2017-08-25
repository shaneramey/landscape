from .cluster import Cluster
from .helm import apply_tiller

class TerraformCluster(Cluster):
    """
    vault write /secret/landscape/clusters/gke_staging-123456_us-west1-a_master cloud_id=staging-123456
    vault write /secret/landscape/clouds/staging-123456 provisioner=terraform
    """
    pass

    def converge(self):
        """
        Checks if a minikube cloud is already running
        Initializes it if not yet running

        Returns:

        """
        print("CONVERGE")
