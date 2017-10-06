import subprocess
import os
import sys
import time
import logging


def helm_add_chart_repos(repos):
    """
    Adds helm chart repos to current user

    Arguments:
     - repos (dict):
        key: chart repo alias
        value: chart repo url

    Returns: None
    """
    for repo_name in repos:
        repo_url = repos[repo_name]
        logging.info("Adding Helm Chart Repo {0} at {1}".format(repo_name, repo_url))
        helm_add_chart_repo(repo_name, repo_url)

def helm_add_chart_repo(repo_alias, url):
    """
    Adds a single helm chart repo

    Arguments:
     - repo_alias (string): used to remotely identify/pull helm chart packages
     - url (string): url for chart repo

    Returns: None
    """
    repo_add_cmd = "helm repo add {0} {1}".format(repo_alias, url)
    subprocess.call(repo_add_cmd, shell=True)


def helm_repo_update():
    """
    Updates the local Helm repository index of available charts
    """
    repo_update_cmd = 'helm repo update'
    subprocess.call(repo_update_cmd, shell=True)


def apply_tiller():
    """
    Checks if Tiller is already installed. If not, install it.
    """
    tiller_pod_status_cmd = 'kubectl get pod --namespace=kube-system ' + \
                            '-l app=helm -l name=tiller ' + \
                            '-o jsonpath=\'{.items[0].status.phase}\''
    logging.info('Checking tiller status with command: ' + tiller_pod_status_cmd)

    proc = subprocess.Popen(tiller_pod_status_cmd, stdout=subprocess.PIPE, shell=True)
    tiller_pod_status = proc.stdout.read().rstrip().decode()

    # if Tiller isn't initialized, wait for it to come up
    if not tiller_pod_status == "Running":
        logging.info('Did not detect tiller pod')
        init_tiller()
    else:
        logging.info('Detected running tiller pod')
    # make sure Tiller is ready to accept connections
    wait_for_tiller_ready(tiller_pod_status_cmd)


def init_tiller():
    """
    Creates Tiller RBAC permissions and initializes Tiller
    """
    serviceaccount_create_command = 'kubectl create serviceaccount --namespace=kube-system tiller'
    logging.info('Setting up Tiller serviceaccount with command: ' + serviceaccount_create_command)
    subprocess.call(serviceaccount_create_command, shell=True)
    
    clusterrolebinding_create_command = 'kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller'
    logging.info('Setting up Tiller ClusterRoleBinding: ' + clusterrolebinding_create_command)
    subprocess.call(clusterrolebinding_create_command, shell=True)
    
    helm_provision_command = 'helm init --service-account=tiller'
    logging.info('Initializing Tiller with command: ' + helm_provision_command)
    subprocess.call(helm_provision_command, shell=True)


def wait_for_tiller_ready(monitor_command):
    """
    Sleep until Tiller is ready
    """
    devnull = open(os.devnull, 'w')
    proc = subprocess.Popen(monitor_command, stdout=subprocess.PIPE, stderr=devnull, shell=True)
    tiller_pod_status = proc.stdout.read().rstrip().decode()
    if tiller_pod_status == "Running":
        logging.info('tiller pod already running')
    else:
        logging.info('Waiting for tiller pod to be ready')
        while tiller_pod_status != "Running":
            proc = subprocess.Popen(monitor_command, stdout=subprocess.PIPE, stderr=devnull, shell=True)
            tiller_pod_status = proc.stdout.read().rstrip().decode()
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1) 
        warm_up_seconds = 7
        logging.info("Sleeping {0} seconds to allow tiller to warm-up".format(warm_up_seconds))
        time.sleep(warm_up_seconds)
