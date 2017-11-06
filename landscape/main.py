#! /usr/bin/env python3

"""
Usage: landscape [options]
        cloud (list [--git-branch=<git_branch> | --all-branches] [--cluster=<cluster_name>] | 
               converge [--cloud=<cloud_project>])
       landscape [options]
        cluster [--cluster=<cluster_name>] [--cloud=<cloud_name>] (list 
         [--git-branch=<git_branch> | --all-branches] |
         converge [--converge-cloud])
       landscape [options]
        charts [--namespaces=<namespaces>] [--cluster=<cluster_name>] (list 
         | converge [--converge-cluster] [--converge-localmachine])
       landscape [options]
        secrets overwrite-vault-with-lastpass 
         --secrets-username=<lpass_user> 
         [--dangerous-overwrite-vault] 
         [--shared-secrets-folder=<pass_folder>] 
         [--shared-secrets-item=<pass_folder_item>] 
         [--secrets-password=<lpass_password>]
       landscape [options]
        setup install-prerequisites

Options:
    --all-branches               When listing resources, list all git-branches
    --dry-run                    Simulate, but don't converge.
    --log-level=<log_level>      Log messages at least this level [default: INFO].
    --dangerous-overwrite-vault  Allow VAULT_ADDR != http://127.0.0.1:8200 [default: false].
    --shared-secrets-folder=<pass_folder>     [default: Shared-k8s/k8s-landscaper].
    --shared-secrets-item=<pass_folder_item>  [default: GIT_BRANCH_NAME].
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
    git_branch_cmd = "git branch"

    logging.debug("Running {0}".format(git_branch_cmd))
    proc = subprocess.Popen(git_branch_cmd, stdout=subprocess.PIPE, shell=True)
    git_branch_cmd_output = proc.stdout.read().rstrip().decode()
    # wait for command return code
    proc.communicate()[0]
    if proc.returncode != 0:
        raise ChildProcessError('Could not detect git branch. Try passing --git-branch')

    git_branch_cmd_lines = git_branch_cmd_output.splitlines()
    starred_branchname = next((item for item in git_branch_cmd_lines if item.startswith('*')))
    current_branch = starred_branchname.strip()[2:]
    logging.info("Auto-detected cwd branch to be: " + current_branch)

    return current_branch

def main():
    args = docopt.docopt(__doc__)
    # option to skip application of plans
    dry_run = args['--dry-run']

    # parse and apply logging verbosity
    loglevel = args['--log-level']
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    # parse arguments
    cloud_selection = args['--cloud']
    cluster_selection = args['--cluster']
    namespaces_selection = args['--namespaces']

    # branch is used to pull secrets from Vault, and to distinguish clusters
    git_branch_selection = args['--git-branch']
    if not git_branch_selection:
        git_branch_selection = git_branch()
    
    use_all_git_branches = args['--all-branches']
    if use_all_git_branches:
        git_branch_selection = None

    if namespaces_selection:
        deploy_only_these_namespaces = namespaces_selection.split(',')
    else:
        deploy_only_these_namespaces = []
    also_converge_cloud = args['--converge-cloud']
    also_converge_cluster = args['--converge-cluster']
    also_converge_localmachine = args['--converge-localmachine']
    # if set, write to a VAULT_ADDR env variable besides http://127.0.0.1:8200
    remote_vault_ok = args['--dangerous-overwrite-vault']

    # landscape cloud ...
    if args['cloud']:
        logging.debug("git_branch_selection: {0}".format(git_branch_selection))
        clouds = CloudCollection(git_branch_selection)
        logging.debug("clouds: {0}".format(clouds))
        # landscape cloud list
        if args['list']:
            if cluster_selection:
                clusters = ClusterCollection(clouds, cloud_selection, git_branch_selection)
                cluster_cloud = cloud_for_cluster(clouds, clusters, cluster_selection)
                print(cluster_cloud.name)
            else:
                print(clouds)
        # landscape cloud converge
        elif args['converge']:
            clouds[cloud_selection].converge(dry_run)

    # landscape cluster ...
    elif args['cluster']:
        clouds = CloudCollection(git_branch_selection)
        clusters = ClusterCollection(clouds, cloud_selection, git_branch_selection)
        # landscape cluster list
        if args['list']:
            print(clusters)
        elif args['converge']:
            if also_converge_cloud:
                cluster_cloud.converge()
            clusters[cluster_selection].converge(dry_run)

    # landscape charts ...
    elif args['charts']:
        clouds = CloudCollection(git_branch_selection)
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
        if args['overwrite-vault-with-lastpass']:
            central_secrets_folder = args['--shared-secrets-folder']
            central_secrets_item = args['--shared-secrets-item']
            if central_secrets_item == 'GIT_BRANCH_NAME':
                central_secrets_item = git_branch_selection
            central_secrets_username = args['--secrets-username']
            central_secrets_password = args['--secrets-password']
            shared_secrets = UniversalSecrets(provider='lastpass', username=central_secrets_username, password=central_secrets_password)
            shared_secrets.overwrite_vault(shared_secrets_folder=central_secrets_folder, shared_secrets_item=git_branch_selection, use_remote_vault=remote_vault_ok, simulate=dry_run)

    # landscape setup install-prerequisites ...
    elif args['setup']:
        if args['install-prerequisites']:
            install_prerequisites(platform.system())

if __name__ == "__main__":
    main()
