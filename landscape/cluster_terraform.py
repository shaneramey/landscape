import subprocess

from .cluster import Cluster

class TerraformCluster(Cluster):
    """
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """
    pass

    def __init__(self, **kwargs):
        self.google_credentials = kwargs['google_credentials']
        super(TerraformCluster, self).__init__(**kwargs)

    def cluster_setup(self):
        """
        Checks if a terraform cloud is already running
        Initializes it if not yet running

        Returns:

        """
        gce_auth_cmd = "gcloud auth activate-service-account " + \
                        "landscape@staging-165617.iam.gserviceaccount.com " + \
                        "--key-file=/Users/sramey/Downloads/staging-f68d7bef83ba.json"
        return gce_auth_cmd


    def write_gcloud_keyfile_json():
        
    def configure_kubectl(self):

        # self.gce_project = gce_project
        # self.terraform_templates_dir = tf_templates_dir

        # vault_path_to_creds = '/secret/terraform/{0}/auth'.format(gce_project)
        # creds = self.read_vault_path_item(vault_path_to_creds, 'credentials')

        # encoded_creds_with_newlines = creds.encode('utf-8')
        # encoded_creds = re.sub(r"\n", " ", encoded_creds_with_newlines)
        # os.environ['GOOGLE_CREDENTIALS'] = encoded_creds

        gke_cluster_name = "master"
        gce_zone = "us-west1-a"
        configure_kubecfg_cmd = "gcloud --project={0} " + \
                                "container clusters get-credentials {1} " + \
                                "--zone={2} && " + \
                                "kubectl config use-context {3}".format(self.cloud_id,
                                                                        gke_cluster_name,
                                                                        gce_zone,
                                                                        self.name
                                    )
        print("configure_kubecfg_cmd={0}".format(configure_kubecfg_cmd))
        configure_kubectl_failed = subprocess.call(configure_kubecfg_cmd, shell=True)
        if create_failed:
            sys.exit("ERROR: non-zero retval for {}".format(configure_kubecfg_cmd))
