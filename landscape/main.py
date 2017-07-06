#! /usr/bin/env python3

"""landscape: deploy Helm charts

Usage:
  landscape deploy [--provisioner=<provisioner] [--cluster-domain=<domain>] [--gce-project-id=<gce_project_name>]
  landscape environment
  landscape test
  landscape verify
  landscape report
  landscape purge
  landscape csr

Options:
  --provisioner=<provisioner>             k8s provisioner [default: minikube].
  --cluster-domain=<domain>               Domain used for inside-cluster DNS [default: cluster.local]
  --gce-project-id=<gce_project_name>     In GCE environment, which project ID to use
  --ns=<namespace>                        deploy charts in specified namespace
  --all-namespaces                        deploy charts in all namespaces

Provisioner can be one of minikube, terraform
"""

import docopt
import os
import sys
import subprocess

from . import DEFAULT_OPTIONS
from .cluster import provision_cluster
from .landscaper import deploy_helm_charts
from .utils import (git_get_branch, kubernetes_set_context)
# from .vault import gke_get_region_for_project_name
from . import verify
from . import report
from . import purge
from . import csr


def main():
    # terraform
    # a gce deployment is composed of
    #  - project name
    #
    # a gke deployment is composed of:
    #  - branch name
    args = docopt.docopt(__doc__)
    k8s_provisioner  = args['--provisioner']
    gce_project_name = args['--gce-project-id']
    # not useful for gke deployments; it's always cluster.local there
    cluster_domain   = args['--cluster-domain']

    # gets branch of current working directory
    git_branch_name = git_get_branch()
    k8s_context = get_k8s_context_for_provisioner(k8s_provisioner, gce_project_name, git_branch_name)
    print("k8s_context={0}".format(k8s_context))
    if args['deploy']:
        provision_cluster(provisioner=k8s_provisioner, dns_domain=cluster_domain, project_id=gce_project_name)

        kubernetes_set_context(kube_context)
        deploy_helm_charts()


def get_k8s_context_for_provisioner(provisioner, project_name, git_branch_name):
    if provisioner == 'terraform':
      git_branch_name = 'master'
      region = gce_get_region_for_project_and_branch_deployment(project_name, git_branch_name)
      return "gke_{0}_{1}_{2}".format(project_name, region, git_branch_name)
    else:
      # covers minikube
      return provisioner


def gce_get_region_for_project_and_branch_deployment(gce_project, git_branch):
  """
  Returns a region based on the gce_project + git_branch of a GCE deployment
  """
  return 'us-west1-a'


if __name__ == "__main__":
    main()


