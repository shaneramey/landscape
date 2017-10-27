import subprocess
import json
import os
import sys
import logging

from .cluster import Cluster

class UnmanagedCluster(Cluster):
    """
    Represents an unmanaged Cluster

    Secrets path must exist as:
    vault write /secret/landscape/clusters/$cluster_name cloud_id=unmanaged
    vault write /secret/landscape/clouds/unmanaged provisioner=unmanaged
    """

    def __init__(self, **kwargs):
        super(UnmanagedCluster, self).__init__(**kwargs)
        self.cluster_name = kwargs['context_id']
        self.k8s_credentials = {
            'apiserver': kwargs['kubernetes_apiserver'],
            'client_key': kwargs['kubernetes_client_key'],
            'client_certificate': kwargs['kubernetes_client_certificate'],
            'apiserver_ca': kwargs['kubernetes_apiserver_cacert'],
        }

    def converge(self):
        """
        Converge an unmanaged Kubernetes cluster
        """
        self.configure_kubectl()


    def configure_kubectl(self):
        """
        Retrieves cluster credentials from gcloud command and sets up profile
        """
        cluster_name = self.cluster_name
        user_name = cluster_name
        context_name = cluster_name
        credentials = self.k8s_credentials
        shcmds = []
        kubectl_user_attrs = {
            'client-certificate-data': credentials['client_certificate'],
            'client-key-data': credentials['client_key'],
        }

        kubectl_cluster_attrs = {
            'server': credentials['apiserver'],
            'certificate-authority-data': credentials['apiserver_ca'],
        }

        kubectl_context_attrs = {
            'cluster': cluster_name,
            'user': user_name,
        }

        for user_attr, user_val in kubectl_user_attrs.items():
            shcmds.append("kubectl config set users.{0}.{1} {2}".format(user_name, user_attr, user_val))

        for cluster_attr, cluster_val in kubectl_cluster_attrs.items():
            shcmds.append("kubectl config set clusters.{0}.{1} {2}".format(cluster_name, cluster_attr, cluster_val))

        for context_attr, context_val in kubectl_context_attrs.items():
            shcmds.append("kubectl config set contexts.{0}.{1} {2}".format(context_name, context_attr, context_val))

        # kubectl config set clusters.cluster[cluster_name].'server' credentials['apiserver']
        # kubectl config set clusters.cluster[cluster_name].'certificate-authority-data' credentials['apiserver_ca']
        # kubectl config set users.user[user_name].'client-certificate-data' credentials['client_certificate']
        # kubectl config set users.user[user_name].'client-key-data' credentials['client_key']
        # kubectl config set contexts.context[context_name].'cluster' = cluster_name
        # kubectl config set contexts.context[context_name].'user' = user_name

        for kubectl_cfg_cmd in shcmds:
            cfg_failed = subprocess.call(kubectl_cfg_cmd, shell=True)
            if cfg_failed:
                sys.exit("ERROR: non-zero retval for {}".format(kubectl_cfg_cmd))

        # configure_kubectl_cmd = "kubectl config use-context {0}".format(context_name)
        # logging.info("running command {0}".format(configure_kubectl_cmd))
        # configure_kubectl_failed = subprocess.call(configure_kubectl_cmd, shell=True)
        # if configure_kubectl_failed:
        #     sys.exit("ERROR: non-zero retval for {}".format(configure_kubectl_cmd))

