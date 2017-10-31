import subprocess
import sys

from .cluster import Cluster

class UnmanagedCluster(Cluster):
    """An unmanaged Cluster.

    A cluster that was provisioned in a cloud outside of this tool. Pulled from
    Vault at paths:
        vault write /secret/landscape/clusters/$cluster_name cloud_id=unmanaged
        vault write /secret/landscape/clouds/unmanaged provisioner=unmanaged

    Attributes:
        cluster_name: A string containing the Kubernetes context/cluster name
        k8s_credentials: A dict of API server endpoint + credentials info
    """

    def __init__(self, **kwargs):
        """initializes a UnmanagedCluster

        Reads cluster parameters from Vault for a non-Terraform and non-minikube
        cluster, that was provisioned and remains managed outside of this tool.

        Args:
            kwargs**:
              context_id: String representing the context/name for the
                Kubernetes cluster
              kubernetes_apiserver: URL of the Kubernetes API Server
                for the cluster
              kubernetes_client_key: base64-encoded client auth key
              kubernetes_client_certificate: base64-encoded client cert
              kubernetes_apiserver_cacert: base64-encoded server CA cert

        Returns:
            None.

        Raises:
            None.
        """

        super(UnmanagedCluster, self).__init__(**kwargs)
        self.cluster_name = kwargs['context_id']
        self.k8s_credentials = {
            'apiserver': kwargs['kubernetes_apiserver'],
            'client_key': kwargs['kubernetes_client_key'],
            'client_certificate': kwargs['kubernetes_client_certificate'],
            'apiserver_ca': kwargs['kubernetes_apiserver_cacert'],
        }

    def converge(self):
        """Converge an unmanaged Kubernetes cluster.

        Configures credentials in $KUBECONFIG (typically ~/.kube/config) to connect
        to an unmanaged cluster.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self.configure_kubectl_credentials()


    def _configure_kubectl_credentials(self):
        """Configures credentials from Vault for an unmanaged Kubernetes
        cluster. Set the current context for `kubectl`

        Configures credentials in $KUBECONFIG (typically ~/.kube/config) to
        connect to an unmanaged cluster.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        cluster_name = self.cluster_name
        user_name = cluster_name
        context_name = cluster_name
        credentials = self.k8s_credentials
        
        # Attributes for kubeconfig file
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

        # Generate list of commands to run, to set kubeconfig settings
        shcmds = []
        for user_attr, user_val in kubectl_user_attrs.items():
            shcmds.append("kubectl config set users.{0}.{1} {2}".format(user_name, user_attr, user_val))

        for cluster_attr, cluster_val in kubectl_cluster_attrs.items():
            shcmds.append("kubectl config set clusters.{0}.{1} {2}".format(cluster_name, cluster_attr, cluster_val))

        for context_attr, context_val in kubectl_context_attrs.items():
            shcmds.append("kubectl config set contexts.{0}.{1} {2}".format(context_name, context_attr, context_val))

        # Set kubeconfig via shell commands
        for kubectl_cfg_cmd in shcmds:
            cfg_failed = subprocess.call(kubectl_cfg_cmd, shell=True)
            if cfg_failed:
                sys.exit("ERROR: non-zero retval for {}".format(kubectl_cfg_cmd))

        # configure_kubectl_cmd = "kubectl config use-context {0}".format(self.name)
        # logging.info("running command {0}".format(configure_kubectl_cmd))
        # configure_kubectl_failed = subprocess.call(configure_kubectl_cmd, env=envvars, shell=True)
        # if configure_kubectl_failed:
        #     sys.exit("ERROR: non-zero retval for {}".format(configure_kubectl_cmd))

