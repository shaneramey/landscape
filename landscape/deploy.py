# -*- coding: utf-8 -*-
"""Deploy a cluster and its Helm charts"""
from . import DEFAULT_OPTIONS

import subprocess

def deploy(provisioner='minikube'):
    """Deploy a cluster"""
    start_cmd = DEFAULT_OPTIONS[provisioner]['init_cmd_template']
    subprocess.call("echo {}".format(start_cmd), shell=True)

def provision_cluster(provisioner='minikube'):
    provision(provisioner)