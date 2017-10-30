#! /usr/bin/env python3

"""
landscape: Provisions Kubernetes clusters and Helm charts, with secrets in Hashicorp Vault.


A "cloud" is a single GCE Project ID, or minikube. Currently, only one cloud can be operated on at a time.

A "cluster" is a Kubernetes cluster running within a cloud

"charts" represent a sub-set of charts specific to a cluster

"localmachine" commands operate on the local machine

There may be multiple kubernetes "clusters" within a cloud

Usage:
  landscape cloud list [--git-branch=<terraform_branch>] [--cloud-provisioner=<cloud_provisioner>]
  landscape cloud converge [--cloud=<cloud_project>]
  landscape cluster list [--git-branch=<landscaper_branch>] [--cloud=<cloud_project>] [--cloud-provisioner=<cloud_provisioner>]
  landscape cluster show --cluster=<cluster_name> --cloud-id
  landscape cluster converge --cluster=<cluster_name> [--converge-cloud]
      [--tf-templates-dir=<tf_templates_dir> ] [--debug]
  landscape cluster environment (--write-kubeconfig|--read-kubeconfig) [--kubeconfig-file=<kubecfg>]
  landscape charts list --cluster=<cluster_name> [--provisioner=<cloud_provisioner>]
  landscape charts converge --cluster=<cluster_name> [--chart-dir=<path containing chart defs>]
      [--namespaces=<namespaces>] [--charts=<chart_names>] [--converge-cluster] [--converge-localmachine]
      [--converge-cloud] [--landscaper-branch=<branch_name>]
  landscape secrets overwrite [--secrets-username=<username>] [--from-lastpass] [--shared-secrets-folder=<central_secrets_path>]
  landscape setup install-prerequisites

Options:
  --cloud-provisioner=<cloud_provisioner>      Cloud provisioner [terraform|minikube|unmanaged]
  --cluster=<context_name>                     Operate on cluster context, defined in Vault
  --git-branch=<branch_name>                   List clouds (Terraform) or charts (Landscaper) subscribed to branch (via Vault) 
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
  --from-lastpass                              Fetches values from Lastpass and puts them in Vault
  --shared-secrets-folder=<central_folder>     Location in LastPass to pull secrets from [default: Shared-k8s/k8s-landscaper/master].
  --secrets-username=<username>                Username for central shared secrets repository
  --tf-templates-dir=<tf_templates_dir>        Terraform templates directory [default: ./tf-templates].
  --chart-dir=<path containing chart defs>     Helm Chart deployment directory [default: ./charts].
  --log-level=<log_level>                      Log messages at least this level [default: NOTSET].
  --cloud-id                                   Retrieve cloud-id of cluster (which is pulled from Vault)
Provisioner can be one of minikube, terraform.
"""

import docopt
import os
import subprocess
import logging
import platform

from .cloudcollection import CloudCollection
from .clustercollection import ClusterCollection
from .chartscollection_landscaper import LandscaperChartsCollection
from .secrets import UniversalSecrets
from .localmachine import Localmachine
from .kubernetes import (kubernetes_get_context, kubectl_use_context)
from .vault import (read_kubeconfig, write_kubeconfig)
from .prerequisites import install_prerequisites


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
    logging.basicConfig(level=logging.DEBUG)
    args = docopt.docopt(__doc__)
    cloud_provisioner = args['--cloud-provisioner']
    terraform_definition_root = args['--tf-templates-dir']
    chart_definition_root = args['--chart-dir']
    git_branch_selector = args['--git-branch']
    
    # Check if current branch matches cloud/cluster. TODO: move this to classes
    # if not tf_git_branch_selector:
    #     tf_git_branchname = git_branch()
    # if not ls_git_branchname:
    #     ls_git_branchname = git_branch()

    cluster_selection = args['--cluster']
    # branch is used to pull secrets from Vault, and to distinguish clusters
    namespaces_selection = args['--namespaces']
    if namespaces_selection:
        deploy_only_these_namespaces = namespaces_selection.split(',')
    else:
        deploy_only_these_namespaces = []
    cloud_selection = args['--cloud']
    also_converge_cloud = args['--converge-cloud']
    also_converge_cluster = args['--converge-cluster']
    also_converge_localmachine = args['--converge-localmachine']
    # log_level = args['--log-level']
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # landscape cloud
    if args['cloud']:
        clouds = CloudCollection(cloud_provisioner, terraform_definition_root)
        # landscape cloud list
        if args['list']:
            print(clouds)
        # landscape cloud converge
        elif args['converge']:
            clouds[cloud_selection].converge()
    # landscape cluster
    elif args['cluster']:
        clouds = CloudCollection(cloud_provisioner, terraform_definition_root)
        clusters = ClusterCollection(clouds, git_branch_selector)
        # landscape cluster list
        if args['list']:
            print(clusters)
        elif args['show'] and args['--cloud-id']:
            cluster_cloud = cloud_for_cluster(clouds, clusters, cluster_selection)
            print(cluster_cloud.name)
        elif args['converge']:
            if also_converge_cloud:
                cluster_cloud.converge()
            clusters[cluster_selection].converge()
    # landscape charts
    elif args['charts']:
        clouds = CloudCollection(cloud_provisioner, terraform_definition_root)
        clusters = ClusterCollection(clouds, git_branch_selector)
        cluster_cloud = cloud_for_cluster(clouds, clusters, cluster_selection)
        # TODO: figure out cluster_provisioner inside LandscaperChartsCollection
        cluster_provisioner = cluster_cloud['provisioner']
        charts = LandscaperChartsCollection(cluster_selection, chart_definition_root, cluster_provisioner, deploy_only_these_namespaces)
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
            # set up local machine for cluster
            if also_converge_localmachine:
                localmachine = Localmachine(cluster=clusters[cluster_selection])
                localmachine.converge()
    # landscape secrets
    elif args['secrets']:
        # landscape secrets overwrite --from-lastpass
        if args['overwrite'] and args['--from-lastpass']:
            central_secrets_folder = args['--shared-secrets-folder']
            central_secrets_username = args['--secrets-username']
            shared_secrets = UniversalSecrets(provider='lastpass', username=central_secrets_username)
            shared_secrets.overwrite_vault(shared_secrets_folder=central_secrets_folder)
    # landscape setup install-prerequisites
    elif args['setup']:
        if args['install-prerequisites']:
            install_prerequisites(platform.system())

if __name__ == "__main__":
    main()
