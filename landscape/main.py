#! /usr/bin/env python3

"""landscape.py: deploy Helm charts

Usage:
  landscape deploy [--provisioner=<provisioner]
  landscape environment
  landscape test
  landscape verify
  landscape report
  landscape purge
  landscape csr

Options:
  --git-branch=<branch>           git branch (default: auto-detect branch)
  --provisioner=<provisioner>     k8s provisioner [default: minikube].
  --ns=<namespace>                deploy charts in specified namespace
  --all-namespaces                deploy charts in all namespaces

Provisioner can be one of minikube, terraform
"""

import docopt
import os
import sys

from . import DEFAULT_OPTIONS
from .deploy import provision_cluster, update_helm_charts
from . import test
from . import deploy
from . import verify
from . import report
from . import purge
from . import csr

sys.argv[0] = 'landscape'

def main():
    print sys.argv
    args = docopt.docopt(__doc__)
    k8s_provisioner = args['--provisioner']
    print "k8s_provisioner={}".format(k8s_provisioner)
    if args['deploy']:
        provision(provisioner=k8s_provisioner)
if __name__ == "__main__":
    main()
