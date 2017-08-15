import subprocess
import os
import sys
import time

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
        print("- Adding Helm Chart Repo {0} at {1}".format(repo_name, repo_url))
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
    print('Checking tiller status with command: ' + tiller_pod_status_cmd)

    proc = subprocess.Popen(tiller_pod_status_cmd, stdout=subprocess.PIPE, shell=True)
    tiller_pod_status = proc.stdout.read().rstrip().decode()

    # if Tiller isn't initialized, wait for it to come up
    if not tiller_pod_status == "Running":
        print('  - did not detect tiller pod')
        init_tiller(tiller_pod_status_cmd)
    else:
        print('  - detected running tiller pod')


def init_tiller(wait_tiller_ready_cmd):
    serviceaccount_create_command = 'kubectl create serviceaccount --namespace=kube-system tiller'
    print('  - Setting up Tiller serviceaccount with command: ' + serviceaccount_create_command)
    subprocess.call(serviceaccount_create_command, shell=True)
    
    clusterrolebinding_create_command = 'kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller'
    print('  - Setting up Tiller ClusterRoleBinding: ' + clusterrolebinding_create_command)
    subprocess.call(clusterrolebinding_create_command, shell=True)
    
    helm_provision_command = 'helm init --service-account=tiller'
    print('  - initializing Tiller with command: ' + helm_provision_command)
    subprocess.call(helm_provision_command, shell=True)
    wait_for_tiller_ready(wait_tiller_ready_cmd)


def wait_for_tiller_ready(monitor_command):
    devnull = open(os.devnull, 'w')
    proc = subprocess.Popen(monitor_command, stdout=subprocess.PIPE, stderr=devnull, shell=True)
    tiller_pod_status = proc.stdout.read().rstrip().decode()

    print('  - waiting for tiller pod to be ready')
    warm_up_seconds = 10
    while tiller_pod_status != "Running":
        proc = subprocess.Popen(monitor_command, stdout=subprocess.PIPE, stderr=devnull, shell=True)
        tiller_pod_status = proc.stdout.read().rstrip().decode()
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(1) 
    print("  - sleeping {0} seconds to allow tiller to warm-up".format(warm_up_seconds))
    time.sleep(warm_up_seconds)
