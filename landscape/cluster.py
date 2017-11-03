import logging
import subprocess
from .kubernetes import kubectl_use_context
from .helm import wait_for_tiller_ready

class Cluster(object):
    """A single generic Kubernetes cluster. Meant to be subclassed.

    Should include methods to initialize a kubernetes cluster and install helm.

    Attributes:
        name: the name of the cluster
        cloud_id: the cloud that provisioned the cluster's ID

    """
    def __init__(self, **kwargs):
        """initializes a Cluster.

        Reads a cluster's definition from Vault.

        Args:
            kwargs**:
              context_id: the Cluster's context name on local machine
              cloud_id: a list of Clouds, one of which should (if defined
              in Vault properly) host the Cluster

        Returns:
            None

        Raises:
            None
        """
        self.name = kwargs['context_id']
        self.cloud_id = kwargs['cloud_id']
        self.landscaper_branch = kwargs['landscaper_branch']


    def __str__(self):
        return self.name


    def converge(self, dry_run):
        """
        Override these methods in your subclass
        """
        self.cluster_setup(dry_run)
        self._configure_kubectl_credentials(dry_run)
        self.apply_tiller(dry_run)


    def apply_tiller(self, dry_run):
        """Checks if Tiller is already installed. If not, install it.

        Retrieves rows pertaining to the given keys from the Table instance
        represented by big_table.  Silly things may happen if
        other_silly_variable is not None.

        Args:
            dry_run: flag for simulating convergence

        Returns:
            None.

        Raises:
            None.
        """
        tiller_pod_status_cmd = 'kubectl get pod --context=' + self.name + \
                                ' --namespace=kube-system ' + \
                                '-l app=helm -l name=tiller ' + \
                                '-o jsonpath=\'{.items[0].status.phase}\''

        if not dry_run:
            logging.info('Checking tiller pod status with command: ' + \
                            tiller_pod_status_cmd)
            proc = subprocess.Popen(tiller_pod_status_cmd,stdout=subprocess.PIPE,
                                    stderr=None, shell=True)
            tiller_pod_status = proc.stdout.read().rstrip().decode()

            # if Tiller isn't initialized, wait for it to come up
            if not tiller_pod_status == "Running":
                logging.info('Did not detect tiller pod')
                self.init_tiller(dry_run)
            else:
                logging.info('Detected running tiller pod')
            # make sure Tiller is ready to accept connections
            wait_for_tiller_ready(tiller_pod_status_cmd)
        else:
            logging.info('DRYRUN: would be Checking tiller pod status with command: ' + \
                            tiller_pod_status_cmd)

    def init_tiller(self, dry_run):
        """Creates Tiller RBAC permissions and initializes Tiller.

        Retrieves rows pertaining to the given keys from the Table instance
        represented by big_table.  Silly things may happen if
        other_silly_variable is not None.

        Args:
            dry_run: flag for simulating convergence

        Returns:
            None.

        Raises:
            None.
        """
        serviceaccount_create_command = 'kubectl create serviceaccount --namespace=kube-system tiller'
        if not dry_run:
            logging.info('Creating Tiller serviceaccount: ' + \
                serviceaccount_create_command)
            subprocess.call(serviceaccount_create_command, shell=True)
        else:
            logging.info('DRYRUN: would be Creating Tiller serviceaccount: ' + \
                    serviceaccount_create_command)

        clusterrolebinding_create_command = 'kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller'
        if not dry_run:
            logging.info('Creating Tiller ClusterRoleBinding: ' + clusterrolebinding_create_command)
            subprocess.call(clusterrolebinding_create_command, shell=True)
        else:
            logging.info('DRYRUN: would be Creating Tiller ClusterRoleBinding: ' + \
                clusterrolebinding_create_command)

        # Initialize Helm by installing Tiller
        helm_provision_command = 'helm init --service-account=tiller'
        if not dry_run:
            logging.info('Initializing Tiller: ' + \
                            helm_provision_command)
            subprocess.call(helm_provision_command, shell=True)
        else:
            logging.info('DRYRUN: would be Initializing Tiller: ' + \
                    helm_provision_command)


    def cluster_setup(self, dry_run):
        raise NotImplementedError('Must be overridden in subclass')


    def _configure_kubectl_credentials(self, dry_run):
        raise NotImplementedError('Must be overridden in subclass')
