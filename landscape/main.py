#! /usr/bin/env python3

"""
Usage: landscape [options] cloud
         (list [--git-branch] [--cluster=<cluster_name>] | 
         converge [--cloud=<cloud_project>])
       landscape [options] cluster
         [--cloud=<cloud_name>] (list 
         | show | converge [--cluster=<cluster_name>] [--converge-cloud])
       landscape [options] charts
         [--namespaces=<namespaces>] (list 
         --cluster=<cluster_name> | show | converge 
         [--converge-cluster] [--converge-localmachine])
       landscape [options] secrets [--namespaces=<namespaces>]
         (list --cluster=<cluster_name> | show | converge 
         [--converge-cluster] [--converge-localmachine])
       landscape [options] secrets overwrite --from-lastpass
         --secrets-username=<lastpass_user> 
         --shared-secrets-folder=<lastpass_folder>

Options:
    --dry-run                  Simulate, but don't converge.
    --log-level=<log_level>    Log messages at least this level [default: INFO].
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
    parent_cloud_id = cluster_collection[cluster_selection].cloud_id
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
    dry_run = args['--dry-run']
    # Check if current branch matches cloud/cluster. TODO: move this to classes
    # if not tf_git_branch_selector:
    #     tf_git_branchname = git_branch()
    # if not ls_git_branchname:
    #     ls_git_branchname = git_branch()

    cloud_selection = args['--cloud']
    cluster_selection = args['--cluster']
    # branch is used to pull secrets from Vault, and to distinguish clusters
    namespaces_selection = args['--namespaces']
    git_branch_selection = args['--git-branch']
    if namespaces_selection:
        deploy_only_these_namespaces = namespaces_selection.split(',')
    else:
        deploy_only_these_namespaces = []
    also_converge_cloud = args['--converge-cloud']
    also_converge_cluster = args['--converge-cluster']
    also_converge_localmachine = args['--converge-localmachine']

    # parse and apply logging verbosity
    loglevel = args['--log-level']
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    # landscape cloud ...
    if args['cloud']:
        clouds = CloudCollection()
        # landscape cloud list
        if args['list']:
            print(clouds)
        # landscape cloud converge
        elif args['converge']:
            clouds[cloud_selection].converge(dry_run)

    # landscape cluster ...
    elif args['cluster']:
        clouds = CloudCollection()
        clusters = ClusterCollection(clouds, cloud_selection, git_branch_selection)
        # landscape cluster list
        if args['list']:
            print(clusters)
        elif args['show'] and args['--cloud-id']:
            cluster_cloud = cloud_for_cluster(clouds, clusters, cluster_selection)
            print(cluster_cloud.name)
        elif args['converge']:
            if also_converge_cloud:
                cluster_cloud.converge()
            clusters[cluster_selection].converge(dry_run)

    # landscape charts ...
    elif args['charts']:
        clouds = CloudCollection()
        clusters = ClusterCollection(clouds, cloud_selection, git_branch_selection)
        cluster_cloud = cloud_for_cluster(clouds, clusters, cluster_selection)
        # TODO: figure out cluster_provisioner inside LandscaperChartsCollection
        cluster_provisioner = cluster_cloud['provisioner']
        charts = LandscaperChartsCollection(cluster_selection, cluster_provisioner, deploy_only_these_namespaces)
        
        # landscape charts list ...
        if args['list']:
            print(charts)

        # landscape charts converge ...
        elif args['converge']:
            if also_converge_cloud:
                cluster_cloud.converge()
            if also_converge_cluster:
                clusters[cluster_selection].converge()
            charts.converge(dry_run)
            # set up local machine for cluster
            if also_converge_localmachine:
                localmachine = Localmachine(cluster=clusters[cluster_selection])
                localmachine.converge()

    # landscape secrets ...
    elif args['secrets']:
        # landscape secrets overwrite --from-lastpass ...
        if args['overwrite'] and args['--from-lastpass']:
            central_secrets_folder = args['--shared-secrets-folder']
            central_secrets_username = args['--secrets-username']
            shared_secrets = UniversalSecrets(provider='lastpass', username=central_secrets_username)
            shared_secrets.overwrite_vault(shared_secrets_folder=central_secrets_folder)

    # landscape setup install-prerequisites ...
    elif args['setup']:
        if args['install-prerequisites']:
            install_prerequisites(platform.system())

if __name__ == "__main__":
    main()
