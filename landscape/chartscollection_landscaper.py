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
        charts: An integer count of the eggs we have laid.
        cluster_branch:  The branch of the landscaper repo that the cluster subscribes to
    """
    def __init__(self, context_name, cluster_cloud_type, namespace_selection, dry_run):
        """Initializes a set of charts for a cluster.

        Determines which yaml files in the directory structure should be applied
        based on cloud provisioner type and optionally a namespace selection.
        For example, minikube gets kube-dns but GKE (via terraform) does not.

        When namespaces=[], deploy all namespaces.

        Args:
            context_name: The Kubernetes context name in which to apply charts.
            cluster_cloud_type: A directory name containing the cluster type.
            namespace_selection: A List of namespaces for which to apply charts.

        Returns:
            None.

        Raises:
            None.
        """

        # Read charts from:
        #  - cluster's cloud type (minikube, terraform (GKE), unmanaged, etc.)
        #  - 'all' dir contains charts which can be applied to all clusters.
        # branch used to read landscaper secrets from Vault (to put in env vars)
        self.__DRYRUN = dry_run
        self._vault = VaultClient()
        self.context_name = context_name
        self.cluster_branch = self.__get_landscaper_branch_that_cluster_subscribes_to()
        self.__chart_collections = ['all'] + [cluster_cloud_type]
        self.charts = self.__load_landscaper_yaml_for_cloud_type_and_namespace_selection(namespace_selection)


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


    def __get_landscaper_branch_that_cluster_subscribes_to(self):
        """Read landscaper branch for cluster name from vault

        Returns:
            landscaper branch for cluster, read from vault (str)
        """
        return self._vault.get_vault_data(
            '/secret/landscape/clusters/' + \
            self.context_name)['landscaper_branch']


    def __load_landscaper_yaml_for_cloud_type_and_namespace_selection(self, select_namespaces):
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


    def converge(self):
        """Read namespaces from charts and apply them one namespace at a time.

        Performs steps:
         - for each namespace in self.charts
         - get secrets from Vault as environment variables
         - run landscaper apply
        """
        namespaces_to_apply = self.__namespaces()
        for namespace in namespaces_to_apply:
            logging.debug("Running deploy_landscaper_charts on namespace {0}".format(namespace))
            envvar_secrets_for_namespace = self.get_landscaper_envvars_for_namespace(namespace)
            # Get list of yaml files
            yamlfiles_in_namespace = [item.filepath for item in self.charts if item.namespace == namespace]
            self.deploy_charts_for_namespace(yamlfiles_in_namespace, namespace, envvar_secrets_for_namespace)


    def __namespaces(self):
        """Returns a list of namespaces defined in all charts for provisioner
           This means all namespaces in 1 of minikube, terraform, or unmanaged
        """
        PRIORTY_NAMESPACES = [
            'auto-approve-csrs',
            'kube-system',
        ]
        sorted_namespaces = []
        nsdict = {}
        all_provisioner_charts = self.charts
        # Generate namespace list by reading every chart's value
        for chart in all_provisioner_charts:
            candidate_ns = getattr(chart, 'namespace')
            if not candidate_ns in nsdict:
                nsdict[candidate_ns] = 1

        # install the high-priority namespaces first
        for priority_namespace in PRIORTY_NAMESPACES:
            if priority_namespace in nsdict:
                sorted_namespaces.append(priority_namespace)

        # install other namespaces
        for normal_namespace in nsdict.keys():
            if not normal_namespace in PRIORTY_NAMESPACES:
                sorted_namespaces.append(normal_namespace)

        return sorted_namespaces


    def get_landscaper_envvars_for_namespace(self, namespace):
        # pull secrets from Vault and apply them as env vars
        secrets_env = {}
        for chart_release_definition in self.charts:
            if chart_release_definition.namespace == namespace and chart_release_definition.secrets:
                chart_secrets_envvars = self.vault_secrets_for_chart(
                                            chart_release_definition.namespace,
                                            chart_release_definition.name)

                # Check if this chart's secrets would conflict with existing
                # environment variables. Update the env vars with them, if not.
                # Generate error message if key already exists.
                for envvar_key, envvar_val in chart_secrets_envvars.items():
                    if envvar_key not in secrets_env:
                        secrets_env[envvar_key] = envvar_val
                    else:
                        raise ValueError("Environment variable {0} already set in environment! Aborting.")

                # check each landscaper yaml secret to make sure it's been pulled
                # from Vault.
                # Build a list of missing secrets
                vault_missing_secrets = []
                for landscaper_secret in chart_release_definition.secrets:
                    # Generate error message if secret(s) missing
                    if landscaper_secret not in secrets_env:
                        vault_missing_secrets.append(landscaper_secret)
                # Report on any missing secrets
                if vault_missing_secrets:
                    for missing_secret in vault_missing_secrets:
                        logging.error('Missing landscaper secret ' + missing_secret)
                    sys.exit(1)

        landscaper_env_vars = self.vault_secrets_to_envvars(secrets_env)
        return landscaper_env_vars


    def deploy_charts_for_namespace(self, landscaper_filepaths, k8s_namespace, envvars):
        """Pulls secrets from Vault and converges charts using Landscaper.

        Helm Tiller must already be installed. Injects environment variables 
        pulled from Vault into local environment variables, so landscaper can
        apply the secrets from Vault.

        Args:
            dry_run: flag for simulating convergence

        Returns:
            None.

        Raises:
            None.
        """
        # list of landscape yaml files to apply
        # Build up a list of namespaces to apply, and deploy them
        # Note: Deploying a single chart is not possible when more than 2
        #       at in a namespace. This is because Landscaper wipes the ns 1st 
        ls_apply_cmd = 'landscaper apply -v --namespace=' + \
                            k8s_namespace + \
                            ' --context=' + self.context_name + \
                            ' ' + ' '.join(landscaper_filepaths)
        if self.__DRYRUN:
            ls_apply_cmd += ' --dry-run'
        logging.info('Executing: ' + ls_apply_cmd)
        # update env to preserve VAULT_ env vars
        os.environ.update(envvars)
        create_failed = subprocess.call(ls_apply_cmd, shell=True)
        if create_failed:
            sys.exit("ERROR: non-zero retval for {}".format(ls_apply_cmd))


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
                                                    self.cluster_branch,
                                                    chart_namespace,
                                                    chart_name
                                                   )
        logging.info("Reading path {0}".format(chart_vault_secret))
        vault_secrets = self._vault.dump_vault_from_prefix(chart_vault_secret, strip_root_key=True)
        return vault_secrets


    def vault_secrets_to_envvars(self, vault_secrets):
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
