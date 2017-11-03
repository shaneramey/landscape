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
