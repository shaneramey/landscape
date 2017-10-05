import platform
import subprocess
import logging
import yaml
import re
import sh

from .kubernetes import kubectl_use_context
from .helm import apply_tiller

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
        self.vm_clouds  = kwargs['cloud_collection']
        self.kubernetes_clusters = kwargs['cluster_collection']


    def converge(self):
        """
        Override this method in your subclass
        """
        print('TODO: (minikube) import CA') # cluster
        print('sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.minikube/ca.crt')
        print('TODO: helm add repos (pulled from where? Vault?)') # cluster
        self.run_vpn_install() # Install Viscosity OpenVPN profile
        print("vm_clouds={0}".format(self.vm_clouds))
        print("kubernetes_clusters={0}".format(self.kubernetes_clusters))


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
