#! /usr/bin/env python3

"""landscape: deploy Helm charts

Usage:
  landscape deploy [--provisioner=<provisioner] [--cluster-domain=<domain>]
  landscape environment
  landscape test
  landscape verify
  landscape report
  landscape purge
  landscape csr

Options:
  --provisioner=<provisioner>             k8s provisioner [default: minikube].
  --cluster-domain=<domain>               Domain used for inside-cluster DNS [default: cluster.local]
  --ns=<namespace>                        deploy charts in specified namespace
  --all-namespaces                        deploy charts in all namespaces

Provisioner can be one of minikube, terraform
"""

import docopt
import os
import sys

from . import DEFAULT_OPTIONS
from .cluster import provision_cluster
from .landscaper import deploy_helm_charts
from . import verify
from . import report
from . import purge
from . import csr


def main():
    args = docopt.docopt(__doc__)
    k8s_provisioner = args['--provisioner']
    cluster_domain  = args['--cluster-domain']
    if args['deploy']:
        provision_cluster(provisioner=k8s_provisioner, dns_domain=cluster_domain)
        deploy_helm_charts()
if __name__ == "__main__":
    main()
