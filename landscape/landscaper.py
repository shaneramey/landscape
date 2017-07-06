# -*- coding: utf-8 -*-
"""
Deploy a cluster and its Helm charts

defines Chart-Sets:
 - charts_core: applied to all Kubernetes clusters
 - charts_minikube: applied to minikube cluster
 - charts_gke: applied to gke cluster

"""
import subprocess as sp
import sys
import os
import hvac
import yaml

from .kubernetes import kubernetes_get_context

def deploy_helm_charts_for_namespace(namespace):
    print(
        "### \
        # Namespace: {} \
        ### \
        \
        Deploying into namespace {}".format(namespace))
    create_namespace_if_needed(namespace)


def create_namespace_if_needed(namespace):
    """
    Checks if namespace exists, and if it doesn't - create it
    """
    need_ns = sp.call("kubectl get ns {}".format(namespace), shell=True)
    if need_ns:
        create_failed = sp.call("kubectl create ns {}".format(namespace))
        if create_failed:
            sys.exit("ERROR: failed to create namespace {}".format(namespace))


def deploy_helm_charts(git_branch):
    minikube_environment = True
    print("Deploying Landscaper charts")
    deploy_chart_set('charts_core', git_branch)
    if minikube_environment:
        deploy_chart_set('charts_minikube', git_branch)


def deploy_chart_set(chart_set_dir, git_branch):
    """
    iterates over directories in a set of charts and runs landscaper on them

    Arguments:
      - chart_set_dir: Directory containing namespace with chart set inside

    Returns: none
    """
    print("Deploying Chart-Set directory {}".format(chart_set_dir))
    for namespace_of_charts in os.listdir(os.getcwd() + '/' + chart_set_dir):
        landscaper_apply_dir(chart_set_dir, namespace_of_charts, git_branch)

def landscaper_set_environment(git_branch, k8s_namespace, helm_chart_name, helm_chart_secrets):
    """
    Pulls secrets from Vault and sets them as Landscaper-compatible env vars

    Arguments:
     - git_branch: pulls secrets from Vault subtree of branch
     - k8s_namespace: deployments pull secrets from Vault into this namespace
     - helm_chart_name: name of the chart being deployed
     - a list of the secret names pulled from the Landscaper yaml

    Returns: None, but environment variables get set
    """
    if 'VAULT_TOKEN' not in os.environ:
        sys.exit("VAULT_TOKEN needed. Please set that in your environment")

    secret_item = "/secret/landscape/{0}/{1}/{2}".format(
                                                    git_branch,
                                                    k8s_namespace,
                                                    helm_chart_name
                                                   )
    print('        - reading Vault subtree: ' + secret_item)

    vault_client = hvac.Client(token=os.environ['VAULT_TOKEN'])
    vault_chart_secrets_item = vault_client.read(secret_item)

    # compare landscaper secrets with vault contents
    # exit with list of secrets set in landscaper yaml but not in vault
    if not vault_chart_secrets_item:
        print("          - no chart secrets in vault")
    else:   
        vault_chart_secrets = vault_chart_secrets_item['data']
        # build list of missing secrets
        vault_missing_secrets = []
        for helm_secret in helm_chart_secrets:
            if helm_secret not in vault_chart_secrets.keys():
                vault_missing_secrets.append(helm_secret)

        # deploy secrets from Vault to environment variables
        if not vault_missing_secrets:
            for key, value in vault_chart_secrets.items():
                landscaper_env_var = helm_secret_name_to_envvar_name(key)
                print("          - setting chart secret {0} in environment variable {1}".format(key, landscaper_env_var))
                os.environ[landscaper_env_var] = value
        else:
            for missing_secret in vault_missing_secrets:
                print('        - missing secret ' + missing_secret)
            sys.exit(1)

def helm_secret_name_to_envvar_name(keyname):
    """
    Translate helm secret name to environment variable
    The environment variable is then read by the landscaper command

    e.g., secret-admin-password becomes SECRET_ADMIN_PASSWORD
    """
    return keyname.replace('-', '_').upper()


def landscaper_apply_dir(chart_set_directory, namespace_directory, git_branch_id):
    """
    Reads current branch from environment
    """
    current_k8s_context = kubernetes_get_context()
    print("  - deploying charts in directory {0}/{1} to namespace {1}".format(
            chart_set_directory,
            namespace_directory
            ))
    # TODO: move chart directory to installation procedure
    chart_directory = chart_set_directory + '/' + namespace_directory

    # apply landscaper chart yaml
    for chart_yaml in os.listdir(os.getcwd() + '/' + chart_directory):
        path_to_ls_yaml = chart_directory + '/' + chart_yaml
        ls_yaml = read_landscaper_yaml(path_to_ls_yaml)
        chart_name = ls_yaml['name']
        print("    - Checking vault for secrets for Helm chart: {0}".format(chart_name))

        if 'secrets' in ls_yaml:
            print("      - Setting secrets")
            chart_secrets = ls_yaml['secrets']
            landscaper_set_environment(git_branch_id, namespace_directory, chart_name, chart_secrets)
        else:
            print("      - No secrets defined")
    ls_apply_cmd = 'landscaper apply -v --namespace=' + namespace_directory + \
                        ' --context=' + current_k8s_context + \
                        " {0}/{1}".format(chart_set_directory, namespace_directory)
    print("    - executing: " + ls_apply_cmd)
    create_failed = sp.call(ls_apply_cmd, shell=True)
    if create_failed:
        sys.exit("ERROR: non-zero retval for {}".format(ls_apply_cmd))


def read_landscaper_yaml(landscaper_yaml_filename):
    """
    Opens a landscaper yaml file definition and returns chart name
    """
    with open(landscaper_yaml_filename, 'r') as fh:
        yml = yaml.load(fh.read())
    return yml
