import os
import glob
import yaml
import subprocess
import sys

from .vault import VaultClient
from .chartscollection import ChartsCollection
from .helm import apply_tiller

class LandscaperChartsCollection(ChartsCollection):
    """ Loads up a directory of chart yaml for use by Landscaper
    vault write /secret/landscape/clouds/staging-165617 provisioner=terraform
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """
    def __init__(self, root_dir, gitbranch, cloud_specific_subset):
        self.chartset_root_dir = root_dir
        # all clouds get common charts
        self.chart_collections = ['__all_clusters__'] + [cloud_specific_subset]
        self.chart_sets = self.__load_chart_sets()
        self.secrets_git_branch = gitbranch
        self.__vault = VaultClient()


    def __str__(self):
        return self.chartset_root_dir

    def __load_chart_sets(self):
        path_to_chartset_root_dir = self.chartset_root_dir
        chart_sets = {}
        for chart_set in os.listdir(path_to_chartset_root_dir):
            if chart_set in self.chart_collections:
                chart_set_charts = [file for file in glob.glob(path_to_chartset_root_dir + '/' + chart_set + '/**/*.yaml', recursive=True)]
                for landscaper_yaml in chart_set_charts:
                    with open(landscaper_yaml) as f:
                        chart_info = yaml.load(f)
                        chart_name = chart_info['name']
                        chart_namespace = chart_info['namespace']
                        if not chart_namespace in chart_sets:
                            chart_sets[chart_namespace] = []
                        chart_info['landscaper_yaml_path'] = landscaper_yaml
                        chart_sets[chart_namespace].append(chart_info)
        return chart_sets


    def converge(self):
        apply_tiller()
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
                            vault_missing_secrets.append(helm_secret)
                    if vault_missing_secrets:
                        for missing_secret in vault_missing_secrets:
                            print('        - missing secret ' + missing_secret)
                        sys.exit(1)
            landscaper_env = self.set_landscaper_envvars(namespace_secrets)
            ls_apply_cmd = 'landscaper apply -v --namespace=' + namespace + \
                                ' ' + ' '.join(yaml_files)
            print("    - executing: " + ls_apply_cmd)
            os.environ.update(landscaper_env)
            create_failed = subprocess.call(ls_apply_cmd, shell=True)
            if create_failed:
                sys.exit("ERROR: non-zero retval for {}".format(ls_apply_cmd))


    def vault_secrets_for_chart(self, chart_namespace, chart_name):
        chart_vault_secret = "/secret/landscape/charts/{0}/{1}/{2}".format(
                                                    self.secrets_git_branch,
                                                    chart_namespace,
                                                    chart_name
                                                   )
        print("Reading path {0}".format(chart_vault_secret))
        vault_secrets = self.__vault.dump_vault_from_prefix(chart_vault_secret, strip_root_key=True)
        return vault_secrets


    def set_landscaper_envvars(self, vault_secrets):
        envvar_list = {}
        for secret_key, secret_value in vault_secrets.items():
            envvar_key = self.helm_secret_name_to_envvar_name(secret_key)
            envvar_list.update({envvar_key: secret_value})
        return envvar_list

    def helm_secret_name_to_envvar_name(self, keyname):
        """
        Translate helm secret name to environment variable
        The environment variable is then read by the landscaper command

        e.g., secret-admin-password becomes SECRET_ADMIN_PASSWORD
        """
        return keyname.replace('-', '_').upper()
