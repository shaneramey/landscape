import subprocess
import sys
import os
import hvac
import re

from .helm import apply_tiller

class TerraformCluster():
    """
    Deploys a terraform cluster

    requires the following environment variables set:
    - VAULT_ADDR
    - VAULT_CACERT
    - VAULT_TOKEN
    """

    def __init__(self, gce_project, tf_templates_dir, debug=False):
        self.gce_project = gce_project
        self.terraform_templates_dir = tf_templates_dir

        vault_path_to_creds = '/secret/terraform/{0}/auth'.format(gce_project)
        creds = self.read_vault_path_item(vault_path_to_creds, 'credentials')

        encoded_creds_with_newlines = creds.encode('utf-8')
        encoded_creds = re.sub(r"\n", " ", encoded_creds_with_newlines)
        os.environ['GOOGLE_CREDENTIALS'] = encoded_creds
        if debug:
            os.environ['TF_LOG'] = 'DEBUG'
        print("encoded_creds={0}".format(encoded_creds))
        print("kubernetes_version={0}".format(k8s_version))
        print("gce_project={0}".format(gce_project))
        print("tf_templates_dir={0}".format(tf_templates_dir))


    def _vault_path_for_project(self):
        vault_path = "/secret/terraform/{0}/gke/master".format(self.gce_project)
        return vault_path


    @property
    def kubernetes_version(self):
        vault_path = self._vault_path_for_project(self.gce_project)
        version = self.read_vault_path_item(vault_path, 'master')
        return version
    
    @property
    def region(self):
        vault_path = '/secret/terraform/{0}/gke/master'
        region = self.read_vault_path_item(vault_path, 'master')
        return "gke_{0}_{1}-{2}_{3}".format(self.gce_project, 'us-west1', 'a', 'master')

    def kubeconfig_context_name(self):
        vault_path = '/secret/terraform/{0}'
        region = self.read_vault_path_item(vault_path, 'master')
        return "gke_{0}_{1}-{2}_{3}".format(self.gce_project, 'us-west1', 'a', 'master')


    def google_creds_for_project(self, gce_project_name):
        """
        Obtains GCE credentials from Vault
        
        Arguments:
         - gce_project_name (str): GCE project ID (e.g., dev-123457)

        Returns: JSON containing GCE credentials (str)
        """
        vault_path = '/secret/terraform/{0}/auth'.format(gce_project_name)
        creds = read_vault_path_item(vault_path, 'credentials')
        return creds


    def read_vault_path_item(self, item_path, element):
        """
        Reads a vault item and returns a specific key
        
        Arguments:
         - item_path (str): Vault path to vault item
         - element (str): element within the vault item

        Returns: element value (str)
        """
        vault_addr = os.environ.get('VAULT_ADDR')
        vault_cacert = os.environ.get('VAULT_CACERT')
        vault_token = os.environ.get('VAULT_TOKEN')
        vault_client = hvac.Client(url=vault_addr,
                                    token=vault_token,
                                    verify=vault_cacert)
        try: 
            creds_vault_item = vault_client.read(item_path)
        except hvac.exceptions.InvalidRequest:
            sys.exit("Failed to read from Vault. Check VAULT_ vars")

        creds_vault_item_data = creds_vault_item['data']
        element_value = creds_vault_item_data[element]
        return element_value


    def start_cluster(self):
        """
        Checks if a minikube cluster is already running
        Initializes it if not yet running

        Returns:

        """
        self.init_cluster()
        terraform_cmd_tmpl = 'terraform validate' + \
            ' && ' + \
            'terraform plan -var="gce_project_id={0}" ' + \
                '-var="gke_cluster1_name={1}" ' + \
                '-var="gke_cluster1_version={2}"' + \
            ' && ' + \
            'terraform apply -var="gce_project_id={0}" ' + \
                '-var="gke_cluster1_name={1}" ' + \
                '-var="gke_cluster1_version={2}"'

        terraform_cmd = terraform_cmd_tmpl.format(self.gce_project,
                                                    'master',
                                                    self.kubernetes_version)
        print('  - applying terraform state with command: ' + terraform_cmd)
        failed_to_apply_terraform = subprocess.call(terraform_cmd,
                                                    cwd=self.terraform_templates_dir,
                                                    env=os.environ,
                                                    shell=True)
        if failed_to_apply_terraform:
            sys.exit('ERROR: terraform command failed')


    def init_cluster(self):
        """
        initializes a terraform cluster
        """
        tf_init_cmd_tmpl = 'terraform init ' + \
                        '-backend-config "bucket=tfstate-{0}" ' + \
                        '-backend-config "path=tfstate-{0}" ' + \
                        '-backend-config "project={0}"'

        tf_init_cmd = tf_init_cmd_tmpl.format(self.gce_project)

        print('  - initializing terraform with command: ' + tf_init_cmd)
        failed_to_init_terraform = subprocess.call(tf_init_cmd,
                                                    cwd=self.terraform_templates_dir,
                                                    env=os.environ,
                                                    shell=True)
        if failed_to_init_terraform:
            sys.exit('ERROR: terraform init failed')


    def get_k8s_context_for_provisioner(self, project_name, git_branch_name):
        """
        Generate a kube context name like what GCE gives in 
        'gcloud --project=staging-123456 container clusters get-credentials master'
        e.g., gke_staging-165617_us-west1-a_master
        """
        region = self.gce_get_zone_for_project_and_branch_deployment(project_name, git_branch_name)
        return "gke_{0}_{1}_{2}".format(project_name, region, git_branch_name)


    def gce_get_zone_for_project_and_branch_deployment(self, gce_project, git_branch):
      """
      Reads zone from Vault based on gce_project + git_branch of a GCE deployment.
      """

      return 'us-west1-a'

    def post_cluster_init_actions(self):
        apply_tiller()
        self.get_gke_credentials(self.terraform_templates_dir)

    def get_gke_credentials(self, tf_template_dir):
        """
        Pull GKE kubernetes credentials from GCE and writes to ~/.kube/config

        Returns: None, but gke credentials should be in ~/.kube/config
        """
        credentials_cmd = 'terraform output get-credentials-command'
        print('  - obtaining terraform script with command: ' + credentials_cmd)
        proc = subprocess.Popen(credentials_cmd, cwd=tf_template_dir, stdout=subprocess.PIPE, shell=True)
        get_credentials_command = proc.stdout.read().rstrip().decode()
        print('  - getting credentials with command: ' + get_credentials_command)
        failed_to_set_creds = subprocess.call(get_credentials_command, cwd=tf_template_dir, shell=True)
        if failed_to_set_creds:
            sys.exit('ERROR: failed to obtain credentials and/or set them')