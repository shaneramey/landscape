import os
import fnmatch
import yaml
import subprocess
import sys

from .vault import VaultClient
from .chartscollection import ChartsCollection
from .helm import apply_tiller

class LandscaperChartsCollection(ChartsCollection):
    """Loads up a directory of chart yaml for use by Landscaper

    vault write /secret/landscape/clouds/staging-123456 provisioner=terraform
    vault write /secret/landscape/clouds/minikube provisioner=minikube

    Attributes:
        kube_context: A boolean indicating if we like SPAM or not.
        chartset_root_dir: An integer count of the eggs we have laid.
        chart_collections: An integer count of the eggs we have laid.
        namespaces: An integer count of the eggs we have laid.
        chart_sets: An integer count of the eggs we have laid.
        secrets_git_branch: An integer count of the eggs we have laid.
    """

    def __init__(self, context_name, root_dir, cloud_specific_subset, namespaces):
        """Fetches rows from a Bigtable.

        Retrieves rows pertaining to the given keys from the Table instance
        represented by big_table.  Silly things may happen if
        other_silly_variable is not None.

        Args:
            big_table: An open Bigtable Table instance.
            keys: A sequence of strings representing the key of each table row
                to fetch.
            other_silly_variable: Another optional variable, that has a much
                longer name than the other args, and which does nothing.

        Returns:
            A dict mapping keys to the corresponding table row data
            fetched. Each row is represented as a tuple of strings. For
            example:

            {'Serak': ('Rigel VII', 'Preparer'),
             'Zim': ('Irk', 'Invader'),
             'Lrrr': ('Omicron Persei 8', 'Emperor')}

            If a key from the keys argument is missing from the dictionary,
            then that row was not found in the table.

        Raises:
            IOError: An error occurred accessing the bigtable.Table object.
        """
        self.kube_context = context_name
        self.chartset_root_dir = root_dir
        # all clouds get common charts
        self.chart_collections = ['__all_cloud_provisioners__'] + [cloud_specific_subset]
        self.namespaces = namespaces
        self.chart_sets = self.__load_chart_sets()
        self.__vault = VaultClient()
        self.secrets_git_branch = self.__vault.get_vault_data('/secret/landscape/clusters/' + self.kube_context)['landscaper_branch']


    def __str__(self):
        """Returns a list of charts.

        The chart list returned will be a key-value pair of the format:
        ${namespace}-${chart_name}.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        return self.chartset_root_dir


    def __load_chart_sets(self):
        """Loads the set of charts for a specific cluster.

        Different provisioners deploy a different set of charts under a 
        directory structure on a single branch.

        Args:
            None.

        Returns:
            A dict of namespaces with the charts in each namespace inside.

        Raises:
            None.
        """
        path_to_chartset_root_dir = self.chartset_root_dir
        chart_sets = {}
        namespaces = self.namespaces
        for chart_set in os.listdir(path_to_chartset_root_dir):
            if chart_set in self.chart_collections:
                chart_set_charts = []
                for root, dirnames, filenames in os.walk(path_to_chartset_root_dir + '/' + chart_set):
                    for filename in fnmatch.filter(filenames, '*.yaml'):
                        chart_set_charts.append(os.path.join(root, filename))
                for landscaper_yaml in chart_set_charts:
                    with open(landscaper_yaml) as f:
                        chart_info = yaml.load(f)
                        chart_name = chart_info['name']
                        chart_namespace = chart_info['namespace']
                        # check to see if chart in selected list of namespaces
                        if not namespaces or chart_namespace in namespaces:
                            if not chart_namespace in chart_sets:
                                chart_sets[chart_namespace] = []
                            chart_info['landscaper_yaml_path'] = landscaper_yaml
                            chart_sets[chart_namespace].append(chart_info)
        return chart_sets


    def converge(self):
        """Pulls secrets from Vault and converges using Landscaper.

        Helm Tiller must already be installed. Injects environment variables 
        pulled from Vault into local environment variables, so landscaper can
        apply the secrets from Vault

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        k8s_context = self.kube_context
        for namespace in self.chart_sets.keys():
            yaml_files = [] # which landscape yaml files to apply in namespace
            for chart in self.chart_sets[namespace]:
                name = chart['name']
                chart_namespace = chart['namespace']
                yaml_file = chart['landscaper_yaml_path']
                yaml_files.append(yaml_file)
                namespace_secrets = {}
                if 'secrets' in chart:
                    # capture and report on missing Vault secrets
                    vault_missing_secrets = []
                    secrets = chart['secrets']
                    namespace_secrets.update(self.vault_secrets_for_chart(namespace, name))
                    for yaml_secret in secrets:
                        if yaml_secret not in namespace_secrets.keys():
                            vault_missing_secrets.append(yaml_secret)
                    if vault_missing_secrets:
                        for missing_secret in vault_missing_secrets:
                            print(' - missing landscaper secret ' + missing_secret)
                        sys.exit(1)
            landscaper_env = self.set_landscaper_envvars(namespace_secrets)
            ls_apply_cmd = 'landscaper apply -v --namespace=' + namespace + \
                                ' --context=' + k8s_context + \
                                ' ' + ' '.join(yaml_files)
            print("    - executing: " + ls_apply_cmd)
            os.environ.update(landscaper_env)
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
