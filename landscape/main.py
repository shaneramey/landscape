#! /usr/bin/env python3

"""
landscape: Provisions Kubernetes clusters and Helm charts, with secrets in Hashicorp Vault.

Operates on a single cloud, minikube, or GCE project at a time

A "cloud" is a single GCE project, or minikube
A "cluster" is a Kubernetes cluster
There may be multiple kubernetes "clusters" within a cloud

Usage:
  landscape cloud list [--cloud-provisioner=<cloud_provisioner>]
  landscape cloud converge [--cloud=<cloud_project>]
  landscape cluster list [--cloud=<cloud_project>] [--cloud-provisioner=<cloud_provisioner>]
  landscape cluster converge --cluster=<cluster_name> [--converge-cloud]
      [--tf-templates-dir=<tf_templates_dir> ] [--debug]
  landscape cluster environment (--write-kubeconfig|--read-kubeconfig) [--kubeconfig-file=<kubecfg>]
  landscape charts list --cluster=<cluster_name> [--provisioner=<cloud_provisioner>]
  landscape charts converge --cluster=<cluster_name> [--chart-dir=<path containing chart defs>]
      [--namespaces=<namespace>] [--converge-cluster] [--converge-cloud] [--git-branch=<branch_name>]
  landscape prerequisites install

Options:
  --cloud-provisioner=<cloud_provisioner>      Cloud provisioner ("terraform" or "minikube")
  --cluster=<context_name>                     Operate on cluster context, defined in Vault
  --git-branch=<branch_name>                   Git branch to use for secrets lookup
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
  --fetch-lastpass                             Fetches values from Lastpass and puts them in Vault
  --tf-templates-dir=<tf_templates_dir>        Terraform templates directory [default: ./tf-templates].
  --chart-dir=<path containing chart defs>     Helm Chart deployment directory [default: ./charts].
  --debug                                      Run in debug mode.
Provisioner can be one of minikube, terraform.
"""

import docopt
import os
import subprocess

from .cloudcollection import CloudCollection
from .clustercollection import ClusterCollection
from .chartscollection_landscaper import LandscaperChartsCollection
from .kubernetes import (kubernetes_get_context, kubectl_use_context)
from .vault import (read_kubeconfig, write_kubeconfig)
from .prerequisites import install_prerequisites


def list_clouds(cloud_collection):
    """Prints a list of cloud names for a given CloudCollection

    Args:
        cloud_collection (CloudCollection): a set of Cloud objects

    Returns:
        None
    """
    for cloud_name in cloud_collection.list():
        print(cloud_name)


def list_clusters(cluster_collection):
    """Prints a list of cluster names for a given ClusterCollection

    Args:
        cluster_collection (ClusterCollection): a set of Cluster objects

    Returns:
        None
    """
    for cluster_name in cluster_collection.list():
        print(cluster_name)


def list_charts(chart_collection):
    """Prints a list of cluster names for a given ClusterCollection

    Args:
        cluster_collection (ClusterCollection): a set of Cluster objects

    Returns:
        None
    """
    for chart_name in chart_collection.list():
        print(chart_name)


def cloud_for_cluster(cloud_collection, cluster_collection, cluster_selection):
    """Finds and returns the Cloud given a cluster's name

    Takes a collection containing Cloud objects (CloudCollection), a collection
    containing Cluster objects (ClusterCollection) - then looks up the cluster
    name based on the passed cluster_selection inside of the ClusterCollection,
    and returns it

    Args:
        cloud_collection (CloudCollection): A set Cloud objects
        cluster_collection (ClusterCollection): A set of Cluster objects
        cluster_selection (str): Another optional variable, that has a much
            longer name than the other args, and which does nothing.

    Returns:
        Cloud that contains the Cluster with the given name
    """
    parent_cloud_id = cluster_collection[cluster_selection]['cloud_id']
    parent_cloud = cloud_collection[parent_cloud_id]
    return parent_cloud

def git_branch():
    """Gets the git branch of the current working directory

    Takes a collection containing Cloud objects (CloudCollection), a collection
    containing Cluster objects (ClusterCollection) - then looks up the cluster
    name based on the passed cluster_selection inside of the ClusterCollection,
    and returns it

    Args:
        cloud_collection (CloudCollection): A set Cloud objects
        cluster_collection (ClusterCollection): A set of Cluster objects
        cluster_selection (str): Another optional variable, that has a much
            longer name than the other args, and which does nothing.

    Returns:
        git branch of current directory (str)
    """
    git_branch_cmd = "git branch | grep \* | cut -d ' ' -f2"
    proc = subprocess.Popen(git_branch_cmd, stdout=subprocess.PIPE, shell=True)
    current_branch = proc.stdout.read().rstrip().decode()
    return current_branch

def main():
    args = docopt.docopt(__doc__)
    cloud_provisioner = args['--cloud-provisioner']
    terraform_definition_root = args['--tf-templates-dir']
    clouds = CloudCollection(cloud_provisioner, terraform_definition_root)
    clusters = ClusterCollection(clouds)
    chart_definition_root = args['--chart-dir']
    git_branchname = args['--git-branch']
    if not git_branchname:
        git_branchname = git_branch()
    cluster_selection = args['--cluster']
    if cluster_selection:
        cluster_cloud = cloud_for_cluster(clouds, clusters, cluster_selection)
        charts = LandscaperChartsCollection(chart_definition_root, git_branchname, cluster_cloud['provisioner'])
    # branch is used to pull secrets from Vault, and to distinguish clusters
    namespaces_selection = args['--namespaces']
    cloud_selection = args['--cloud']
    also_converge_cloud = args['--converge-cloud']
    also_converge_cluster = args['--converge-cluster']
    # landscape cloud
    if args['cloud']:
        # landscape cloud list
        if args['list']:
            list_clouds(clouds)
        # landscape cloud converge
        elif args['converge']:
            clouds[cloud_selection].converge()
    # landscape cluster
    elif args['cluster']:
        # landscape cloud list
        if args['list']:
            list_clusters(clusters)
        elif args['converge']:
            if also_converge_cloud:
                cluster_cloud.converge()
            clusters[cluster_selection].converge()
    # landscape charts
    elif args['charts']:
        # landscape charts list
        if args['list']:
            list_charts(charts)
        # landscape charts converge
        elif args['converge']:
            if also_converge_cloud:
                cluster_cloud.converge()
            if also_converge_cluster:
                clusters[cluster_selection].converge()
            charts.converge()
    # landscape prerequisites install
    elif args['prerequisites'] and args['install']:
        install_prerequisites()

if __name__ == "__main__":
    main()
