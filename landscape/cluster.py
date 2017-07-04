# -*- coding: utf-8 -*-
"""Deploy a cluster and its Helm charts"""
from . import DEFAULT_OPTIONS

import subprocess
import sys
import time
import os

def provision_cluster(provisioner, dns_domain):
    """
    initializes a cluster

    Arguments:
      provisioner: 

    """

    print("Converging cluster")
    # Start cluster
    if provisioner == 'minikube':
        apply_minikube_cluster(provisioner, dns_domain)
    if provisioner == 'terraform':
        apply_terraform_cluster(provisioner, dns_domain)
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


def apply_terraform_cluster(provisioner, dns_domain):
    """
    creates or converges a terraform-provisioned cluster to its desired-state

    Arguments:
     - provisioner: minikube or terraform
     - dns_domain: dns domain to use for cluster

    Returns: None
    """
    apply_terraform_cmd = DEFAULT_OPTIONS['terraform']['init_cmd_template']
    failed_to_apply_terraform = subprocess.call(apply_terraform_cmd, shell=True)
    if failed_to_apply_terraform:
        print('ERROR: failed to disable addons')


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

def deploy_helm_charts():
    """Deploy a cluster"""

def deploy(provisioner='minikube'):
    """Deploy a cluster"""
    print("placeholder for breaking out minikube vs terraform")


#! /usr/bin/env bash

# initializes a terraform cluster.
# 
#
# Requires tfstate storage backend
# to create:
# export GOOGLE_APPLICATION_CREDENTIALS=downloaded-serviceaccount.json
#terraform init  -backend-config 'bucket=something-something-1234' \
#                -backend-config 'path=tfstate-dev-123456/master.tfstate' \
#                -backend-config 'project=dev-123456'
# - or possibly set (https://github.com/google/google-auth-library-ruby/issues/65#issuecomment-198532641) 
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_EMAIL=
# GOOGLE_ACCOUNT_TYPE=
# GOOGLE_PRIVATE_KEY= ?
