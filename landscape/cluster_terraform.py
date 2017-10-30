import subprocess
import json
import os
import sys
import logging

from .cluster import Cluster

class TerraformCluster(Cluster):
    """A Terraform-provisioned GKE Cluster

    A Cluster provisioned via Terraform google_container_cluster resource.
    Requires the Cluster to completely inside one GCP "project", which is due to
    The current terraform template being an all-in-one template.

    Vault at paths:

    vault write /secret/landscape/clusters/$cluster_name cloud_id=gcp_project_id
    vault write /secret/landscape/clouds/gcp_project_id provisioner=terraform

    gcp_project_id is the target used by the terraform "vpc.tf" template

    Attributes:
        google_credentials: GOOGLE_APPLICATION_CREDENTIALS for terraform auth
        cluster_name: A string containing the Kubernetes context/cluster name
    """


    def __init__(self, **kwargs):
        """initializes a TerraformCluster

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

        super(TerraformCluster, self).__init__(**kwargs)
        self.google_credentials = kwargs['google_credentials']
        self.cluster_name = kwargs['gke_cluster_name']
        self.__cluster_zone = kwargs['gke_cluster_zone']
        self.__gcloud_auth_jsonfile = os.getcwd() + '/cluster-serviceaccount-' + self.name + '.json'
        self.write_gcloud_keyfile_json()

    def cluster_setup(self):
        """Activates authentication for bringing up a Terraform cluster

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """

        envvars = self.__update_environment_vars_with_gcp_auth()
        gce_auth_cmd = "gcloud auth activate-service-account " + \
                        self.service_account_email() + \
                        " --key-file=" + self.__gcloud_auth_jsonfile
        logging.info("Running command {0}".format(gce_auth_cmd))
        gce_auth_failed = subprocess.call(gce_auth_cmd, env=envvars, shell=True)
        if gce_auth_failed:
            sys.exit("ERROR: non-zero retval for {}".format(gce_auth_cmd))


    def __update_environment_vars_with_gcp_auth(self):
        """Update environment variables with GCE credentials file path

        Retrieves rows pertaining to the given keys from the Table instance
        represented by big_table.  Silly things may happen if
        other_silly_variable is not None.

        Args:
            None.

        Returns:
            A dict of the current environment variables with an added
            GOOGLE_APPLICATION_CREDENTIALS variable.

        Raises:
            None.
        """

        return os.environ.update({
            'GOOGLE_APPLICATION_CREDENTIALS': self.__gcloud_auth_jsonfile,
        })


    def service_account_email(self):
        """Returns client_email from current GCP credentials

        Args:
            None.

        Returns:
            A String containing the Google client authentication email address.

        Raises:
            None.
        """

        gce_creds = json.loads(self.google_credentials)
        return gce_creds['client_email']


    def write_gcloud_keyfile_json(self):
        """Writes GOOGLE_APPLICATION_CREDENTIALS-compatible json

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """

        gce_creds_file = self.__gcloud_auth_jsonfile
        logging.debug("Writing GOOGLE_APPLICATION_CREDENTIALS to {0}".format(gce_creds_file))
        f = open(gce_creds_file, "w")
        f = open(self.__gcloud_auth_jsonfile, "w")
        f.write(self.google_credentials)
        f.close()


    def _configure_kubectl_credentials(self):
        """Obtains GKE cluster credentials and sets local k8s-context to cluster

        Gets GKE credentials via already-authenticated client GCP session.  Set
        the current context for `kubectl`

        Configures credentials in $KUBECONFIG (typically ~/.kube/config) to
        connect to an unmanaged cluster.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """

        get_creds_cmd = "gcloud container clusters get-credentials --project={0} --zone={1} {2}".format(self.cloud_id, self.__cluster_zone, self.cluster_name)
        envvars = self.__update_environment_vars_with_gcp_auth()
        logging.info("Running command {0}".format(get_creds_cmd))
        get_creds_failed = subprocess.call(get_creds_cmd, env=envvars, shell=True)
        if get_creds_failed:
            sys.exit("ERROR: non-zero retval for {}".format(get_creds_cmd))

        # set client kubernetes context
        # configure_kubectl_cmd = "kubectl config use-context {0}".format(self.name)
        # logging.info("running command {0}".format(configure_kubectl_cmd))
        # configure_kubectl_failed = subprocess.call(configure_kubectl_cmd, env=envvars, shell=True)
        # if configure_kubectl_failed:
        #     sys.exit("ERROR: non-zero retval for {}".format(configure_kubectl_cmd))
