# -*- coding: utf-8 -*-
"""
Deploy a cluster and its Helm charts

defines Chart-Sets:
 - charts_core: applied to all Kubernetes clusters
 - charts_minikube: applied to minikube cluster
 - charts_gke: applied to gke cluster

"""
import subprocess as sp
import sys
import os
import hvac
import yaml
import glob
import re

from .kubernetes import provisioner_from_context_name
from .helm import helm_repo_update


class ChartSetCollection(object):

    def __init__(self, top_chart_dir, context_id, select_namespaces=[]):
        self.top_chart_dir = top_chart_dir
        self.kubernetes_context = context_id
        self.provisioner = provisioner_from_context_name(context_id)

        all_charts = self.all_chart_files()
        provisioner_chart_sets = self.chart_sets_for_provisioner(all_charts, self.provisioner)
        self.cluster_charts = self.charts_in_namespace(provisioner_chart_sets, select_namespaces)


    def converge(self):
        for chart_set in self.cluster_charts:
            for namespace in self.cluster_charts[chart_set]:
                chart_yaml_files = []
                for chart in self.cluster_charts[chart_set][namespace]:
                    chart_yaml_files.append(self.cluster_charts[chart_set][namespace][chart]['file'])
                self.apply_charts_to_namespace(self.kubernetes_context, namespace, chart_yaml_files, 'master')


    def chart_sets_for_provisioner(self, chart_supersets, provisioner_name):
        chartsets = self.chart_dirs_for_provisioner(provisioner_name)
        selection = {}
        for chart_superset in chart_supersets:
            if chart_superset in chartsets:
                selection.update({ chart_superset: chart_supersets[chart_superset]})
        return selection


    def charts_in_namespace(self, chart_supersets, namespace_selection):
        selection = {}
        if not namespace_selection:
            selection = chart_supersets
        else:
            for chart_superset in chart_supersets:
                for namespace in chart_supersets[chart_superset]:
                    if namespace in namespace_selection:
                        selection.update({ chart_superset: { namespace: chart_supersets[chart_superset][namespace] }})
        return selection

    def chart_name_in_landscaper_yaml(self, landscaper_file):
        with open(landscaper_file, 'r') as stream:
            try:
                return yaml.load(stream)['name']
            except yaml.YAMLError as exc:
                print(exc)


    def namespace_dirpaths_in_landscaper_directory(self, landscaper_chart_directory):
        """
        Returns list of namespace directories
        """
        dirs = os.listdir(landscaper_chart_directory)
        return ['{0}/{1}'.format(landscaper_chart_directory, dir) for dir in dirs]


    def charts_in_namespace_dirpath(self, namespace_dirpath):
        charts = os.listdir(namespace_dirpath)
        return ['{0}/{1}/{2}'.format(self.top_chart_dir, namespace_dirpath, chart) for chart in charts]



    def helm_secret_name_to_envvar_name(self, keyname):
        """
        Translate helm secret name to environment variable
        The environment variable is then read by the landscaper command

        e.g., secret-admin-password becomes SECRET_ADMIN_PASSWORD
        """
        return keyname.replace('-', '_').upper()

        
    def apply_charts_to_namespace(self, kubecfg_context, namespace, chart_yaml_files, git_branch_id):
        """
        Reads current branch from environment

        Reads Landscaper YAML
        Sets secrets as environment variables (pulls from Vault)
        """
        # apply landscaper chart yaml
        namespace_secrets = {}
        for chart_yaml_file in chart_yaml_files:
            print("  - deploying to context: {0} namespace: {1} landscaper file: {2} secret subset: {3}".format(
                    kubecfg_context,
                    namespace,
                    chart_yaml_file,
                    git_branch_id,
                    ))

            ls_yaml = self.read_landscaper_yaml(chart_yaml_file)
            chart_name = ls_yaml['name']
            print("    - Checking vault for secrets for Helm chart: {0}".format(chart_name))

            if 'secrets' in ls_yaml:
                print("      - Setting secrets")
                chart_secrets = ls_yaml['secrets']
                chart_secrets = self.vault_secrets_for_namespace(git_branch_id, namespace, chart_name, chart_secrets)
                print("chart_secrets={0}".format(chart_secrets))
                namespace_secrets.update(chart_secrets)
            else:
                print("      - No secrets defined")
        os.environ.update(namespace_secrets)
        ls_apply_cmd = 'landscaper apply -v --namespace=' + namespace + \
                            ' --context=' + kubecfg_context + \
                            ' ' + ' '.join(chart_yaml_files)
        print("    - executing: " + ls_apply_cmd)
        create_failed = sp.call(ls_apply_cmd, shell=True)
        if create_failed:
            sys.exit("ERROR: non-zero retval for {}".format(ls_apply_cmd))


    def vault_secrets_for_namespace(self, git_branch, k8s_namespace, helm_chart_name, helm_chart_secrets):
        """
        Pulls secrets from Vault and sets them as Landscaper-compatible env vars

        Arguments:
         - git_branch: pulls secrets from Vault subtree of branch
         - k8s_namespace: deployments pull secrets from Vault into this namespace
         - helm_chart_name: name of the chart being deployed
         - a list of the secret names pulled from the Landscaper yaml

        Returns: set of k=v environment variables
        """
        env_vars_for_namespace = {}
        if 'VAULT_TOKEN' not in os.environ:
            sys.exit("VAULT_TOKEN needed. Please set that in your environment")

        secret_item = "/secret/landscape/{0}/{1}/{2}".format(
                                                        git_branch,
                                                        k8s_namespace,
                                                        helm_chart_name
                                                       )
        print('        - reading Vault subtree: ' + secret_item)

        vault_client = hvac.Client(url=os.environ['VAULT_ADDR'],
                                    token=os.environ['VAULT_TOKEN'],
                                    verify=False)
        vault_chart_secrets_item = vault_client.read(secret_item)

        # compare landscaper secrets with vault contents
        # exit with list of secrets set in landscaper yaml but not in vault
        if not vault_chart_secrets_item:
            print("          - no chart secrets in vault")
        else:
            vault_chart_secrets = vault_chart_secrets_item['data']
            # build list of missing secrets
            vault_missing_secrets = []
            for helm_secret in helm_chart_secrets:
                if helm_secret not in vault_chart_secrets.keys():
                    vault_missing_secrets.append(helm_secret)

            # deploy secrets from Vault to environment variables
            if not vault_missing_secrets:
                for key, value in vault_chart_secrets.items():
                    landscaper_env_var = self.helm_secret_name_to_envvar_name(key)
                    print("          - setting chart secret {0} in environment variable {1}".format(key, landscaper_env_var))
                    env_vars_for_namespace[landscaper_env_var] = value
            else:
                for missing_secret in vault_missing_secrets:
                    print('        - missing secret ' + missing_secret)
                sys.exit(1)
        return env_vars_for_namespace
