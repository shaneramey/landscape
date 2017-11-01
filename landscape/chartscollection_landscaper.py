import os
import fnmatch
import yaml
import subprocess
import sys
import logging

from .vault import VaultClient
from .chartscollection import ChartsCollection
from .chart_landscaper import LandscaperChart

class LandscaperChartsCollection(ChartsCollection):
    """Loads up a directory of chart yaml for use by Landscaper

    vault write /secret/landscape/clouds/staging-123456 provisioner=terraform
    vault write /secret/landscape/clouds/minikube provisioner=minikube

    Attributes:
        kube_context: Kubernetes context for landscaper apply command
        namespaces: An integer count of the eggs we have laid.
        charts: An integer count of the eggs we have laid.
        secrets_git_branch: An integer count of the eggs we have laid.
    """
    def __init__(self, context_name, custom_chart_set, namespace_selection):
        """Initializes a set of charts for a cluster.

        When namespaces=[], deploy all namespaces.
        TODO: move cloud_specific_subset logic to within each cluster

        Args:
            context_name: The Kubernetes context name in which to apply charts
            custom_chart_set: A directory name containing the cluster type
            namespaces: A List of namespaces for which to apply charts.

        Returns:
            None.

        Raises:
            None.
        """
        # cluster_selection, cluster_provisioner, deploy_only_these_namespaces

        self.kube_context = context_name
        self.__namespace_selection = namespace_selection
        # all clouds get common charts
        self.__chart_collections = ['all'] + [custom_chart_set]
        self.charts = self.__charts_for_namespaces(namespace_selection)
        self.__vault = VaultClient()
        self.secrets_git_branch = self.__vault.get_vault_data(
            '/secret/landscape/clusters/' + \
            self.kube_context)['landscaper_branch']


    def __str__(self):
        """Pretty-prints a list of clusters

        Args:
            self: the current object

        Returns:
            A new-line separated str of charts in format:
            namespace/chart_name

        Raises:
            None.
        """
        output_lines = []
        for chart in self.list():
            output_lines.append(str(chart))

        return '\n'.join(output_lines)


    def list(self):
        """Lists charts"""
        return self.charts


    def __charts_for_namespaces(self, select_namespaces):
        """Loads Landscaper YAML files into a List if they are in namespaces
        
        Checks inside YAML file for namespace field and appends LandscaperChart
        to converge-charts list

        Args:
            select_namespaces: A list of namespaces to apply. If None, apply all

        Returns:
            A list of LandscaperChart chart definitions.

        Raises:
            None.
        """
        cluster_specific_landscaper_dirs = self.__chart_collections

        landscaper_dirpath = ['./charts/' + s for s in self.__chart_collections]
        files = self.__landscaper_filenames_in_dirs(landscaper_dirpath)
        charts = []
        for landscaper_yaml in files:
            with open(landscaper_yaml) as f:
                chart_info = yaml.load(f)
                logging.debug("chart_info={0}".format(chart_info))
                chart_namespace = chart_info['namespace']
                logging.debug("chart_namespace={0}".format(chart_namespace))
                # load the chart if it matches a namespace selector list param
                # or if there's no namespace selector list, load all
                if chart_namespace in select_namespaces or not select_namespaces:
                    # Add path to landscaper yaml inside Chart object
                    chart_info['filepath'] = landscaper_yaml
                    chart = LandscaperChart(**chart_info)
                    charts.append(chart)

        return charts


    def __landscaper_filenames_in_dirs(self, dirs_to_apply):
        """Generates a list of Landscaper files in specified directories

        Args:
            dirs_to_apply: List of paths to cluster-specific landscaper dirs

        Returns:
            A List of Landscaper files in the specified directories

        Raises:
            None.
        """
        landscaper_files = []
        for cloud_specific_charts_dir in dirs_to_apply:
            if cloud_specific_charts_dir in dirs_to_apply:
                for root, dirnames, filenames in os.walk(cloud_specific_charts_dir):
                    for filename in fnmatch.filter(filenames, '*.yaml'):
                        landscaper_files.append(os.path.join(root, filename))
        logging.debug("landscaper_files={0}".format(landscaper_files))
        return landscaper_files


    def converge(self, dry_run):
        """Applies charts to a single kubernetes context/cluster.

        Args:
            dry_run: flag for simulating convergence

        Returns:
            None.

        Raises:
            None.
        """
        self.helm_repo_update(dry_run)
        self.deploy_landscaper_charts(dry_run)


    def deploy_charts_for_namespace(self, k8s_namespace, dry_run):
        """Pulls secrets from Vault and converges charts using Landscaper.

        Helm Tiller must already be installed. Injects environment variables 
        pulled from Vault into local environment variables, so landscaper can
        apply the secrets from Vault

        Args:
            dry_run: flag for simulating convergence

        Returns:
            None.

        Raises:
            None.
        """
        k8s_context = self.kube_context
        # list of landscape yaml files to apply
        # Build up a list of namespaces to apply, and deploy them
        # Note: Deploying a single chart is not possible when more than 2
        #       at in a namespace. This is because Landscaper wipes the ns 1st 
        yaml_files = []
        for chart in self.charts:
            # deploy only charts in this namespace
            if getattr(chart, 'namespace') == k8s_namespace:
                yaml_file = chart.filepath
                yaml_files.append(yaml_file)
                # keep a list of conflicting secrets in namespace
                namespace_secrets = {}
                # capture and report on missing Vault secrets
                vault_missing_secrets = []
                if chart.secrets:
                    chart_secret_values = self.vault_secrets_for_chart(
                                            chart.namespace, chart.name)
                    namespace_secrets.update(chart_secret_values)
                    for yaml_secret in chart.secrets:
                        if yaml_secret not in namespace_secrets.keys():
                            vault_missing_secrets.append(yaml_secret)
                if vault_missing_secrets:
                    for missing_secret in vault_missing_secrets:
                        print(' - missing landscaper secret ' + missing_secret)
                    sys.exit(1)
                landscaper_env = self.set_landscaper_envvars(namespace_secrets)
                ls_apply_cmd = 'landscaper apply -v --namespace=' + chart.namespace + \
                                    ' --context=' + k8s_context + \
                                    ' ' + ' '.join(yaml_files)
                if dry_run:
                    ls_apply_cmd += ' --dry-run'
                print("    - executing: " + ls_apply_cmd)
                os.environ.update(landscaper_env)
                create_failed = subprocess.call(ls_apply_cmd, shell=True)
                if create_failed:
                    sys.exit("ERROR: non-zero retval for {}".format(ls_apply_cmd))


    def deploy_landscaper_charts(self, dry_run):
        namespaces_to_apply = self.__namespaces()
        for namespace in namespaces_to_apply:
            self.deploy_charts_for_namespace(namespace, dry_run)

        # Deploy kube-system first

    def __namespaces(self):
        deploy_these_namespaces = []
        nsdict = {}
        all_provisioner_charts = self.charts
        # Generate namespace list by reading every chart's value
        for chart in all_provisioner_charts:
            candidate_ns = getattr(chart, 'namespace')
            if not candidate_ns in nsdict:
                nsdict[candidate_ns] = 1

        return nsdict.keys()

    def helm_repo_update(self, dry_run):
        """Updates the local Helm repository index of available charts.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        repo_update_cmd = 'helm repo update'
        if not dry_run:
            print("    - executing: " + repo_update_cmd)
            subprocess.call(repo_update_cmd, shell=True)
        else:
            print("    - DRYRUN would execute: " + repo_update_cmd)


    def vault_secrets_for_chart(self, chart_namespace, chart_name):
        """Read Vault secrets for a deployment (chart name + namespace).

        Args:
            chart_namespace: The namespace where the chart will be installed.
            chart_name: The name of the chart being installed.

        Returns:
            A dict of Vault secrets, pulled from a deployment-specific key

        Raises:
            None.
        """
        chart_vault_secret = "/secret/landscape/charts/{0}/{1}/{2}".format(
                                                    self.secrets_git_branch,
                                                    chart_namespace,
                                                    chart_name
                                                   )
        print("Reading path {0}".format(chart_vault_secret))
        vault_secrets = self.__vault.dump_vault_from_prefix(chart_vault_secret, strip_root_key=True)
        return vault_secrets


    def set_landscaper_envvars(self, vault_secrets):
        """Converts secrets pulled from Vault to environment variables.

        Used by Landscaper to inject environment variables into secrets.

        Args:
            vault_secrets: A dict of secrets, typically pulled from Vault.

        Returns:
            A dict of secrets, converted to landscaper-compatible environment
            variables.

        Raises:
            None.
        """
        envvar_list = {}
        for secret_key, secret_value in vault_secrets.items():
            envvar_key = self.helm_secret_name_to_envvar_name(secret_key)
            envvar_list.update({envvar_key: secret_value})
        return envvar_list


    def helm_secret_name_to_envvar_name(self, keyname):
        """Translate helm secret name to environment variable.

        The environment variable is then read by the landscaper command

        e.g., secret-admin-password becomes SECRET_ADMIN_PASSWORD

        Args:
            keyname: A String of the environment variable name.

        Returns:
            A String converted to capitalized environment variable.

        Raises:
            None.
        """
        return keyname.replace('-', '_').upper()
