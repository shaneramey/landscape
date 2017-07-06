# -*- coding: utf-8 -*-
"""Various helper utilities"""

import subprocess
import re

def namespace_exists(namespace):
    if subprocess.call(['kubectl', 'get', 'ns', namespace], shell=True):
        return True
    else:
        return False
	

def git_get_branch():
	return subprocess.check_output(['git', 'symbolic-ref', 'HEAD', '--short' ]).rstrip()


def test_dns_domain(k8s_provisioner, cluster_dns_domain):
    """
    Validate DNS domain.
    GKE-only supports cluster.local for now, so enforce that

    Returns:
        True if domain validates
        False if domain validation fails
    """
    if k8s_provisioner == 'terraform' and cluster_dns_domain != 'cluster.local':
        return False
    if valid_cluster_domain(cluster_dns_domain):
        return True

def valid_cluster_domain(domain):
    """
    Returns True if DNS domain validates
    """
    return re.match('[a-z]{1,63}\.local', domain)


