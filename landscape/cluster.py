import subprocess
import sys
import os
import hvac
import re

class LandscapeCluster(object):
    """Abstract base-class of Kubernetes provisioners

    Arguments:
        provision(provisioner obj): k8s provisioner (minikube, terraform, etc)
        config(provisionerConfig obj): provisioner-specific options

    Methods:
        new(
            provisioner=minikube, # or terraform
            gce_project=develop-123456, # GCE project ID
            landscaper_branch=master # Landscape chart-set for environment
            ):
            an object representing a Landscape-provisioned cluster
        deploy():
            Converge cluster towards its desired-state
    """
    @property
    def kubeconfig_context_name(self):
        region = gce_get_zone_for_project_and_branch_deployment(project_name, git_branch_name)
        return "gke_{0}_{1}_{2}".format(project_name, region, git_branch_name)

    @property
    def vault_creds():
        return 
        {
            'VAULT_ADDR': '',
            'VAULT_CACERT': '',
            'VAULT_TOKEN': '',
        }

    def converge(self):
        self.start_cluster()
        self.post_cluster_init_actions()

    def list_clusters():
        vault_addr = os.environ.get('VAULT_ADDR')
        vault_cacert = os.environ.get('VAULT_CACERT')
        vault_token = os.environ.get('VAULT_TOKEN')
        cluster_list_root = '/secret/k8s_contexts'
        k8s_context_names = []

        vault_client = hvac.Client(url=vault_addr,
                                    token=vault_token,
                                    verify=vault_cacert)
        vault_root = vault_client.list(cluster_list_root)
        if vault_root:
            k8s_context_names = vault_client.list(cluster_list_root)['data']['keys']
        return k8s_context_names


class MinikubeCluster(LandscapeCluster):
    """
    Deploys a minikube cluster
    """
    @property
    def kubeconfig_context_name(self):
        return 'minikube'

    def __init__(self, kubernetes_version, minikube_driver, dns_domain):
        self.kubernetes_version = kubernetes_version
        self.minikube_driver = minikube_driver
        self.dns_domain = dns_domain
        print("kubernetes_version={0}".format(kubernetes_version))
        print("minikube_driver={0}".format(minikube_driver))
        print("dns_domain={0}".format(dns_domain))


    def start_cluster(self):
        """
        Checks if a minikube cluster is already running
        Initializes it if not yet running

        Returns:

        """
        status_cmd = 'minikube status --format=\'{{.MinikubeStatus}}\''
        proc = subprocess.Popen(status_cmd, stdout=subprocess.PIPE, shell=True)
        self.cluster_status = proc.stdout.read().rstrip().decode()
        if self.cluster_status == 'Running':
            print('  - cluster previously provisioned. Re-using')
        else:
            print('  - initializing cluster')
            self.initialize_cluster()


    def initialize_cluster(self):
        start_cmd_tmpl = 'minikube start ' + \
                    '--kubernetes-version=v{0} ' + \
                    "--vm-driver={1} " + \
                    "--dns-domain={2} " + \
                    '--extra-config=apiserver.Authorization.Mode=RBAC ' + \
                    '--extra-config=controller-manager.ClusterSigningCertFile=' + \
                    '/var/lib/localkube/certs/ca.crt ' + \
                    '--extra-config=controller-manager.ClusterSigningKeyFile=' + \
                    '/var/lib/localkube/certs/ca.key ' + \
                    '--cpus=8 ' + \
                    '--disk-size=20g ' + \
                    '--memory=8192 ' + \
                    '--docker-env HTTPS_PROXY=$http_proxy ' + \
                    '--docker-env HTTP_PROXY=$https_proxy ' + \
                    '-v=0'
        start_cmd = start_cmd_tmpl.format(self.kubernetes_version,
                                            self.minikube_driver,
                                            self.dns_domain)
        print("start_cmd={0}".format(start_cmd))
        minikube_start_failed = subprocess.call(start_cmd, shell=True)
        if minikube_start_failed:
            sys.exit('ERROR: minikube initialization failure')

    def post_cluster_init_actions(self):
        print('- Configuring minikube addons')
        disable_addons = ['kube-dns', 'registry-creds']
        enable_addons = ['default-storageclass', 'ingress']
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


class TerraformCluster(LandscapeCluster):
    """
    Deploys a terraform cluster

    requires the following environment variables set:
    - VAULT_ADDR
    - VAULT_CACERT
    - VAULT_TOKEN
    """

    def __init__(self, k8s_version, gce_project, tf_templates_dir, debug=False):
        self.kubernetes_version = k8s_version
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
        print(os.environ)
        print("kubernetes_version={0}".format(k8s_version))
        print("gce_project={0}".format(gce_project))
        print("tf_templates_dir={0}".format(tf_templates_dir))


    def google_creds_for_project(self, gce_project_name):
        """
        Obtains GCE credentials from Vault
        
        Arguments:
         - gce_project_name (str): GCE project ID (e.g., dev-123457)

        Returns: JSON containing GCE credentials (str)
        """
        vault_path_to_creds = '/secret/terraform/{0}/auth'.format(gce_project_name)
        creds = read_vault_path_item(vault_path_to_creds, 'credentials')
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

        creds_vault_item = vault_client.read(item_path)
        creds_vault_item_data = creds_vault_item['data']
        element_value = creds_vault_item_data[element]
        return element_value


    def init_cluster(self):
        """
        initializes a terraform cluster
        """
        tf_init_cmd_tmpl = 'terraform init ' + \
                        '-backend-config "bucket=tfstate-{0}"' + \
                        '-backend-config "path=tfstate-{0}"' + \
                        '-backend-config "project={0}"'

        tf_init_cmd = terraform_cmd_tmpl.format(self.gce_project)

        print('  - initializing terraform with command: ' + tf_init_cmd)
        failed_to_init_terraform = subprocess.call(tf_init_cmd,
                                                    cwd=self.terraform_templates_dir,
                                                    env={'TF_LOG': 'DEBUG'},
                                                    shell=True)
        if failed_to_init_terraform:
            sys.exit('ERROR: terraform init failed')


    def start_cluster(self):
        """
        Checks if a minikube cluster is already running
        Initializes it if not yet running

        Returns:

        """
        print("CREDS={0}".format(os.environ['GOOGLE_CREDENTIALS']))
        terraform_cmd_tmpl = 'terraform validate' + \
            ' && ' + \
            'terraform plan -var="gce_project_id={0}" ' + \
                '-var="gke_cluster1_name={1}"' + \
            ' && ' + \
            'terraform apply -var="gce_project_id={0}" ' + \
                '-var="gke_cluster1_name={1}"'

        terraform_cmd = terraform_cmd_tmpl.format(self.gce_project,
                                                    'master')
        print('  - applying terraform state with command: ' + terraform_cmd)
        failed_to_apply_terraform = subprocess.call(terraform_cmd,
                                                    cwd=self.terraform_templates_dir,
                                                    env=os.environ,
                                                    shell=True)
        if failed_to_apply_terraform:
            sys.exit('ERROR: terraform command failed')


    def get_k8s_context_for_provisioner(project_name, git_branch_name):
        """
        Generate a kube context name like what GCE gives in 
        'gcloud --project=staging-123456 container clusters get-credentials master'
        e.g., gke_staging-165617_us-west1-a_master
        """
        region = gce_get_zone_for_project_and_branch_deployment(project_name, git_branch_name)
        return "gke_{0}_{1}_{2}".format(project_name, region, git_branch_name)


    def gce_get_zone_for_project_and_branch_deployment(gce_project, git_branch):
      """
      Reads zone from Vault based on gce_project + git_branch of a GCE deployment.
      """
      return 'us-west1-a'
