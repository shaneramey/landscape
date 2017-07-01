# -*- coding: utf-8 -*-
"""Deploy a cluster and its Helm charts"""
from . import DEFAULT_OPTIONS

import subprocess
import sys

def provision_cluster(provisioner, dns_domain):
    """
    initializes a cluster

    Arguments:
      provisioner: 

    """
    provision_command = start_command_for_provisioner(provisioner, dns_domain)
    subprocess.call(provision_command, shell=True)

def start_command_for_provisioner(provisioner_name, dns_domain_name):
    """
    generate a command to start/converge a cluster

    """
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
    print("hi")


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
