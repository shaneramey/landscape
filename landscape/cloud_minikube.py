import subprocess
import sys
import logging

from .cloud import Cloud

class MinikubeCloud(Cloud):
    """A Minikube-provisioned Virtual Machine

    Secrets path must exist as:
    vault write /secret/landscape/clouds/minikube provisioner=minikube

    Attributes:
        Inherited from superclass.
    """

    def converge(self,dry_run):
        """Converges state of a minikube VM

        Checks if a minikube cloud is already running
        Initializes it if not yet running

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        status_cmd = 'minikube status --format=\'{{.MinikubeStatus}}\''
        proc = subprocess.Popen(status_cmd, stdout=subprocess.PIPE, shell=True)
        cloud_status = proc.stdout.read().rstrip().decode()
        logging.debug('Minikube Cloud status is ' + cloud_status)
        if cloud_status == 'Running':
            if not dry_run:
                logging.info('Re-using previously provisioned cloud')
            else:
                print('DRYRUN: would be Re-using previously provisioned cloud')
        else:
            logging.info('Initializing Cloud')
            if not dry_run:
                self.initialize_cloud()
            else:
                print('DRYRUN: would be Initializing Cloud')


    def initialize_cloud(self):
        """Start minikube.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        start_cmd_tmpl = 'minikube start ' + \
                    '--kubernetes-version=v{0} ' + \
                    "--vm-driver={1} " + \
                    "--dns-domain={2} " + \
                    '--extra-config=apiserver.Authorization.Mode=RBAC ' + \
                    '--extra-config=controller-manager.ClusterSigningCertFile=' + \
                    '/var/lib/localkube/certs/ca.crt ' + \
                    '--extra-config=controller-manager.ClusterSigningKeyFile=' + \
                    '/var/lib/localkube/certs/ca.key ' + \
                    '--cpus=8 ' + \
                    '--disk-size=20g ' + \
                    '--memory=8192 ' + \
                    '--docker-env HTTPS_PROXY=$http_proxy ' + \
                    '--docker-env HTTP_PROXY=$https_proxy ' + \
                    '-v=2'
        start_cmd = start_cmd_tmpl.format('1.8.0',
                                            'xhyve',
                                            'cluster.local')
        logging.info("Starting minikube with command: {0}".format(start_cmd))
        minikube_start_failed = subprocess.call(start_cmd, shell=True)
        if minikube_start_failed:
            sys.exit('ERROR: minikube cloud initialization failure')
