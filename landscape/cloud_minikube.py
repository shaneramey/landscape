import subprocess
import sys

from .cloud import Cloud

class MinikubeCloud(Cloud):
    """
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """
    pass

    def converge(self):
        """
        Checks if a minikube cloud is already running
        Initializes it if not yet running

        Returns:

        """
        status_cmd = 'minikube status --format=\'{{.MinikubeStatus}}\''
        proc = subprocess.Popen(status_cmd, stdout=subprocess.PIPE, shell=True)
        self.cloud_status = proc.stdout.read().rstrip().decode()
        if self.cloud_status == 'Running':
            print('  - cloud previously provisioned. Re-using')
        else:
            print('  - initializing cloud')
            self.initialize_cloud()


    def initialize_cloud(self):
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
                    '-v=99'
        start_cmd = start_cmd_tmpl.format('1.7.5',
                                            'xhyve',
                                            'cluster.local')
        print("start_cmd={0}".format(start_cmd))
        minikube_start_failed = subprocess.call(start_cmd, shell=True)
        if minikube_start_failed:
            sys.exit('ERROR: minikube cloud initialization failure')

