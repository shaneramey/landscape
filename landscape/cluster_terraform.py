import subprocess
import json
import os
import sys

from .cluster import Cluster

class TerraformCluster(Cluster):
    """
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    vault write /secret/landscape/clusters/gke_staging-123456_us-west1-a_master cloud_id=staging-123456 gke_cluster_name=master
    """
    pass


    def __init__(self, **kwargs):
        super(TerraformCluster, self).__init__(**kwargs)
        self.google_credentials = kwargs['google_credentials']
        self.cluster_name = kwargs['gke_cluster_name']
        self.cluster_zone = kwargs['gke_cluster_zone']
        self.gcloud_auth_jsonfile = os.getcwd() + '/cluster-serviceaccount.json'


    def cluster_setup(self):
        """
        Checks if a terraform cloud is already running
        Initializes it if not yet running

        Returns:

        """
        self.write_gcloud_keyfile_json()
        gce_auth_cmd = "gcloud auth activate-service-account " + \
                        self.service_account_email() + \
                        " --key-file=" + self.gcloud_auth_jsonfile
        print("running command {0}".format(gce_auth_cmd))
        return gce_auth_cmd


    def gce_envvars(self):
        return os.environ.update({
            'GOOGLE_APPLICATION_CREDENTIALS': self.gcloud_auth_jsonfile,
        })

    def service_account_email(self):
        gce_creds = json.loads(self.google_credentials)
        return gce_creds['client_email']


    def write_gcloud_keyfile_json(self):
        f = open(self.gcloud_auth_jsonfile, "w")
        f.write(self.google_credentials)
        f.close()


    def configure_kubectl(self):
        get_creds_cmd = "gcloud --project={0} container clusters get-credentials --zone={1} {2}".format(self.cloud_id, self.cluster_zone, self.cluster_name)
        envvars = self.gce_envvars()
        print("running command {0}".format(get_creds_cmd))
        get_creds_failed = subprocess.call(get_creds_cmd, env=envvars, shell=True)
        if get_creds_failed:
            sys.exit("ERROR: non-zero retval for {}".format(get_creds_cmd))

        configure_kubectl_cmd = "kubectl config use-context {0}".format(self.name)
        print("running command {0}".format(configure_kubectl_cmd))
        configure_kubectl_failed = subprocess.call(configure_kubectl_cmd, env=envvars, shell=True)
        if configure_kubectl_failed:
            sys.exit("ERROR: non-zero retval for {}".format(configure_kubectl_cmd))

