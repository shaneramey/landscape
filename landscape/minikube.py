import subprocess
import sys

from .helm import apply_tiller

class MinikubeCluster():
    """
    Deploys a minikube cluster
    """
    @property
    def kubeconfig_context_name(self):
        return 'minikube'


    def __init__(self, kubernetes_version, minikube_driver, dns_domain):
        self.kubernetes_version = kubernetes_version
        self.minikube_driver = minikube_driver
        self.dns_domain = dns_domain
        print("Creating minikube cluster")
        print(" - Kubernetes Version={0}".format(kubernetes_version))
        print(" - Minikube Driver={0}".format(minikube_driver))
        print(" - Cluster DNS Domain={0}".format(dns_domain))


    def converge(self):
        self.start_cluster()
        self.post_cluster_init_actions()


    def start_cluster(self):
        """
        Checks if a minikube cluster is already running
        Initializes it if not yet running

        Returns:

        """
        status_cmd = 'minikube status --format=\'{{.MinikubeStatus}}\''
        proc = subprocess.Popen(status_cmd, stdout=subprocess.PIPE, shell=True)
        self.cluster_status = proc.stdout.read().rstrip().decode()
        if self.cluster_status == 'Running':
            print('  - cluster previously provisioned. Re-using')
        else:
            print('  - initializing cluster')
            self.initialize_cluster()


    def initialize_cluster(self):
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
        start_cmd = start_cmd_tmpl.format(self.kubernetes_version,
                                            self.minikube_driver,
                                            self.dns_domain)
        print("start_cmd={0}".format(start_cmd))
        minikube_start_failed = subprocess.call(start_cmd, shell=True)
        if minikube_start_failed:
            sys.exit('ERROR: minikube initialization failure')


    def post_cluster_init_actions(self):
        print('- Configuring minikube addons')
        disable_addons = ['kube-dns', 'registry-creds', 'ingress']
        enable_addons = ['default-storageclass']
        for disable_addon in disable_addons:
            addon_cmd = "minikube addons disable {0}".format(disable_addon)
            check_cmd_failed = subprocess.call(addon_cmd, shell=True)
            if check_cmd_failed:
                print("ERROR: failed to run command".format(addon_cmd))

        for enable_addon in enable_addons:
            addon_cmd = "minikube addons enable {0}".format(enable_addon)
            check_cmd_failed = subprocess.call(addon_cmd, shell=True)
            if check_cmd_failed:
                print("ERROR: failed to run command".format(addon_cmd))
        apply_tiller()

