import platform
import subprocess
import logging
import yaml
import re
import sh

from .kubernetes import kubectl_use_context

class Localmachine(object):
    """
    Converges local machine for one cluster at a time
    Does:
     - import CA cert (the same CA cert that TLS-enabled pods import)
     - adds helm repo that's authoritative in cluster
       (the same repo used by Jenkins for helm charts)
     - downloads + imports OpenVPN profile to local machine
    vault write /secret/landscape/clusters/minikube cloud_id=minikube
    """

    def __init__(self, **kwargs):
        self.os_platform = platform.system()
        self.kubernetes_cluster = kwargs['cluster']


    def converge(self):
        """
        Override this method in your subclass
        """
        self.helm_add_repos()
        self.import_ca_certificate()
        self.run_vpn_install() # Install Viscosity OpenVPN profile


    def helm_init_client(self):
        helm_init_client_cmd = 'helm init --client-only'
        proc = subprocess.call(helm_init_client_cmd, shell=True)


    def helm_add_repos(self):
        """
        Add local Chartmuseum Helm Chart server
        """
        print('helm repo add chartmuseum http://localhost:8080/')

    def import_ca_certificate(self):
        print('TODO: (minikube) import CA') # cluster
        print('sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.minikube/ca.crt')


    def run_vpn_install(self):
        """
        Installs an OpenVPN profile into the running machine.
        Pulled from the NOTES.txt out of the OpenVPN chart
        """
        get_vpn_profile_cmd = "helm status openvpn-openvpn"
        logging.info("Running command: {0}".format(get_vpn_profile_cmd))
        proc = subprocess.Popen(get_vpn_profile_cmd,
                                                stdout=subprocess.PIPE,
                                                shell=True)
        chart_notes = proc.stdout.read().rstrip().decode()
        yaml_instructions = chart_notes.split('client_commands:')[-1]
        executables_map = yaml.load(yaml_instructions)
        install_profile_cmd = executables_map['generate_openvpn_profile']
        # strip out comments
        raw_command_lines = []
        for command_line in install_profile_cmd.split("\n"):
            if not re.search(r'^\s*#.*', command_line):
                raw_command_lines.append(command_line)

        install_profile_cmd = "\n".join(raw_command_lines)
        logging.info("Running command {0}".format(install_profile_cmd))
        proc = subprocess.call(install_profile_cmd,
                                                shell=True)
