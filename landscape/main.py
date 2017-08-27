#! /usr/bin/env python3

"""
landscape: Provisions Kubernetes clusters and Helm charts, with secrets in Hashicorp Vault.

Operates on a single cloud, minikube, or GCE project at a time

Usage:
  landscape cloud list [--provisioner=<cloud_provisioner>]
  landscape cloud converge [--cloud=<cloud_project>]
  landscape cluster list [--cloud=<cloud_project>]
  landscape cluster converge --cluster=<cluster_name> [--converge-cloud]
      [--provisioner=<provisioner>]
      [--gce-project-id=<gce_project_id>] [--minikube-driver=<driver>] [--kubernetes-version=<k8s_version>] [--cluster-dns-domain=<dns_domain>]
      [--landscaper-git-branch=<git_branch>]
      [--tf-templates-dir=<tf_templates_dir> ] [--debug]
      [--switch-to-cluster-context=<boolean>]
  landscape cluster environment (--write-kubeconfig|--read-kubeconfig) [--kubeconfig-file=<kubecfg>]
  landscape charts list --cluster=<cluster_name> [--provisioner=<cloud_provisioner>]
  landscape charts converge --cluster=<cluster_name> [--chart-dir=<path containing chart defs>]
      [--namespaces=<namespace>] [--charts=<chart_name>] [--converge-cluster] [--converge-cloud]
  landscape prerequisites install

Options:
  --cluster=<context_name>                     Operate on cluster context, defined in Vault
  --write-kubeconfig                           Write ~/.kube/config with contents from Vault
  --read-kubeconfig                            Read ~/.kube/config and put its contents in Vault
  --kubeconfig-file=<kubecfg>                  Specify path to KUBECONFIG [default: ~/.kube/config-landscaper].
  --cloud=<cloud_project>                      k8s cloud provisioner.
  --project=<gce_project_id>                   in GCE environment, which project ID to use. [default: minikube].
  --kubernetes-version=<k8s_version>           in GCE environment, which project ID to use [default: 1.7.0].
  --cluster-dns-domain=<dns_domain>            DNS domain used for inside-cluster DNS [default: cluster.local].
  --minikube-driver=<driver>                   (minikube only) driver type (virtualbox|xhyve) [default: virtualbox].
  --switch-to-cluster-context=<boolean>        switch to kubernetes context after cluster converges [default: true].
  --namespaces=<namespace>                     install only charts under specified namespaces (comma-separated).
  --charts=<charts>                            install only named charts (comma-separated).
  --fetch-lastpass                             Fetches values from Lastpass and puts them in Vault
  --tf-templates-dir=<tf_templates_dir>        Terraform templates directory [default: ./tf-templates].
  --chart-dir=<path containing chart defs>     Helm Chart deployment directory [default: ./charts].
  --debug                                      Run in debug mode.
Provisioner can be one of minikube, terraform.
"""

import docopt
import os

from .cloudcollection import CloudCollection
from .clustercollection import ClusterCollection
from .chartscollection import ChartsCollection
from .client import kubectl_use_context
from .kubernetes import kubernetes_get_context
from .vault import (read_kubeconfig, write_kubeconfig)
from .prerequisites import install_prerequisites

def main():

    clouds = CloudCollection()
    # branch is used to pull secrets from Vault, and to distinguish clusters
    args = docopt.docopt(__doc__)
    cloud_selection = args['--cloud']
    cluster_selection = args['--cluster']
    provisioner = args['--provisioner']
    namespaces = args['--namespaces']
    charts = args['--charts']
    chart_definition_root = args['--chart-dir']
    terraform_definition_root = args['--tf-templates-dir']
    also_converge_cloud = args['--converge-cloud']
    # landscape cloud
    if args['cloud']:
        # landscape cloud list
        if args['list']:
            for cloud_name in clouds.list(provisioner):
                print(cloud_name)
        # landscape cloud converge
        elif args['converge']:
            clouds[cloud_selection].terraform_dir = terraform_definition_root
            clouds[cloud_selection].converge()
    # landscape cluster
    elif args['cluster']:
        # landscape cloud list
        clusters = ClusterCollection()
        if args['list']:
            for cluster_name in clusters.list(cloud_selection):
                print(cluster_name)
        elif args['converge']:
            if also_converge_cloud:
                parent_cloud_id = clusters[cluster_selection]['cloud_id']
                parent_cloud = clouds[parent_cloud_id]
                parent_cloud.terraform_dir = terraform_definition_root
                parent_cloud.converge()
            clusters[cluster_selection].converge()
        # print("clusters={0}".format(clusters))
    # landscape charts
    elif args['charts']:
        all_chart_sets = ChartsCollection(chart_provisioner='landscaper', root=chart_definition_root)
        my_chart_sets = all_chart_sets.charts_for('minikube', [], [])
        if args['list']:
            for chart_set in my_chart_sets:
                print(chart_set)
        elif args['converge']:
            my_chart_sets.converge(namespaces, charts)

    elif args['prerequisites'] and args['install']:
        install_prerequisites()

if __name__ == "__main__":
    main()
