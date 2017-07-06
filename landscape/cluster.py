# -*- coding: utf-8 -*-
"""
Deploy a cluster and its Helm charts

Terraform GKE provider: uses git branch name as index and cluster name

Limitations: git branch name stored in Vault as key.
 This means only one GKE cluster with branch name for each GCE "Project"

"""
from . import DEFAULT_OPTIONS
from .environment import set_gce_credentials
from .terraform import apply_terraform_cluster
import subprocess
import sys
import time
import os

def provision_cluster(provisioner, dns_domain, project_id, git_branch):
    """
    initializes a cluster

    Arguments:
      provisioner: minikube or terraform

    """
    tf_templates_dir = './var/terraform'
    print("Converging cluster")
    # Start cluster
    if provisioner == 'minikube':
        print('Applying minikube cluster')
        apply_minikube_cluster(provisioner, dns_domain)
    if provisioner == 'terraform':
        print('Applying terraform cluster')
        print("proj_id={0}".format(project_id))
        apply_terraform_cluster(provisioner, dns_domain, project_id, tf_templates_dir, git_branch)
    # Provision Helm Tiller
    apply_tiller()


def apply_minikube_cluster(provisioner, dns_domain):
    """
    creates or converges a minikube-provisioned cluster to its desired-state

    Arguments:
     - provisioner: minikube or terraform
     - dns_domain: dns domain to use for cluster

    Returns: None
    """
    minikube_status_cmd = DEFAULT_OPTIONS['minikube']['minikube_status_cmd']
    proc = subprocess.Popen(minikube_status_cmd, stdout=subprocess.PIPE, shell=True)
    minikube_status = proc.stdout.read().rstrip()

    if not minikube_status == 'Running':
        start_minikube(provisioner, dns_domain)
    else:
        print('  - minikube cluster previously provisioned. Re-using ')
    minikube_disable_addons()
    hack_wide_open_security() # FIXME: create ClusterRoles


def start_minikube(provisioner, dns_domain):
    """
    Starts minikube. Prints an error if non-zero exit status
    """
    k8s_provision_command = start_command_for_provisioner(provisioner, dns_domain)
    print('  - running ' + k8s_provision_command)
    minikube_failed = subprocess.call(k8s_provision_command, shell=True)
    print("minikube_failed={}".format(minikube_failed))


def vault_load_gce_creds():
    vault_client = hvac.Client(token=os.environ['VAULT_TOKEN'])

    creds_item = "/secret/terraform/{0}/{1}".format(
                                                    git_branch,
                                                    project_id
                                                   )
    creds_vault_item = vault_client.read(creds_item)

    # compare landscaper secrets with vault contents
    # exit with list of secrets set in landscaper yaml but not in vault
    if not creds_vault_item:
        sys.exit('ERROR: credentials not loaded from Vault')
    else:   
        creds = creds_vault_item['data']
        credentials_json = creds['credentials']


def minikube_disable_addons():
    disable_addons_cmd = DEFAULT_OPTIONS['minikube']['minikube_addons_disable_cmd']
    print('- disabling unused minikube addons ' + disable_addons_cmd)
    print('  - running ' + disable_addons_cmd)
    failed_to_disable_addons = subprocess.call(disable_addons_cmd, shell=True)
    if failed_to_disable_addons:
        print('ERROR: failed to disable addons')


def hack_wide_open_security():
    need_crb = subprocess.call('kubectl get clusterrolebinding ' + \
                                'permissive-binding', shell=True)
    hack_cmd = DEFAULT_OPTIONS['kubernetes']['hack_clusterrolebinding_cmd']
    if need_crb:
        print('  - creating permissive clusterrolebinding')
        print('    - running ' + hack_cmd)
        subprocess.call(hack_cmd, shell=True)
    else:
        print('  - permissive clusterrolebinding already exists ' + hack_cmd)


def apply_tiller():
    """
    Checks if Tiller is already installed. If not, install it.
    """
    helm_provision_command = 'helm init'
    print('  - running ' + helm_provision_command)
    subprocess.call(helm_provision_command, shell=True)

    print('  - waiting for tiller pod to be ready')
    tiller_pod_status = 'Unknown'
    tiller_pod_status_cmd = DEFAULT_OPTIONS['helm']['monitor_tiller_cmd']
    devnull = open(os.devnull, 'w')
    while not tiller_pod_status == "Running":
        proc = subprocess.Popen(tiller_pod_status_cmd, stdout=subprocess.PIPE, stderr=devnull, shell=True)
        tiller_pod_status = proc.stdout.read().rstrip()
        sys.stdout.write('.')
        time.sleep(1)
    time.sleep(2) # need to give tiller a little time to warm up


def start_command_for_provisioner(provisioner_name, dns_domain_name):
    """
    generate a command to start/converge a cluster

    """
    print('Using provisioner: ' + provisioner_name)
    if provisioner_name in DEFAULT_OPTIONS:
        start_cmd_template = DEFAULT_OPTIONS[provisioner_name]['init_cmd_template']
    else:
        sys.exit("provisioner must be minikube or terraform")

    if provisioner_name == "minikube":
        start_cmd = start_cmd_template.format(dns_domain_name, "xhyve")
    elif provisioner_name == "terraform":
        start_cmd = start_cmd_template.format(dns_domain_name)
    return start_cmd


def deploy(provisioner='minikube'):
    """Deploy a cluster"""
    print("placeholder for breaking out minikube vs terraform")