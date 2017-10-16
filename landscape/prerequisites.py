import subprocess as sp
import platform
import os.path
import logging

def install_prerequisites(os_platform):
    """
    Installs prerequisites for the landscape CLI tool

    Returns: None
    """
    install_minikube(os_platform)
    install_lastpass(os_platform)
    install_vault(os_platform)
    install_kubectl(os_platform)
    install_helm(os_platform)
    install_landscaper(os_platform)
    install_terraform(os_platform)
    install_helm_plugins()


def install_minikube(os_platform):
    """Install minikube"""
    install_cmds = {
        'Darwin': 'curl -LO https://storage.googleapis.com/minikube/releases/v0.22.3/minikube-darwin-amd64 && \
        chmod +x minikube-darwin-amd64 && \
        mv minikube-darwin-amd64 /usr/local/bin/minikube'
    }
    dst = '/usr/local/bin/minikube'
    if not os.path.isfile(dst):
        logging.info("installing minikube")
        sp.call(install_cmds[os_platform], shell=True)
    else:
        logging.info("minikube already installed in {0}".format(dst))


def install_lastpass(os_platform):
    """Install LastPass"""
    install_cmds = {
        'Darwin': 'brew update && brew install lastpass-cli --with-pinentry'
    }
    dst = '/usr/local/bin/lpass'
    if not os.path.isfile(dst):
        logging.info("installing lastpass")
        sp.call(install_cmds[os_platform], shell=True)
    else:
        logging.info("lastpass already installed in {0}".format(dst))


def install_vault(os_platform):
    """Installs Hashicorp Vault"""
    install_cmds = {
        'Darwin': 'curl -LO https://releases.hashicorp.com/vault/0.8.3/vault_0.8.3_darwin_amd64.zip && \
        unzip -d /usr/local/bin/ vault_0.8.3_darwin_amd64.zip && \
        rm vault_0.8.3_darwin_amd64.zip'
    }
    dst = '/usr/local/bin/vault'
    if not os.path.isfile(dst):
        logging.info("installing vault")
        sp.call(install_cmds[os_platform], shell=True)
    else:
        logging.info("vault already installed in {0}".format(dst))


def install_kubectl(os_platform):
    """Installs Kubernetes kubectl"""
    install_cmds = {
        'Darwin': 'curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.8.1/bin/darwin/amd64/kubectl && \
        chmod +x kubectl && \
        mv kubectl /usr/local/bin/'
    }
    dst = '/usr/local/bin/kubectl'
    if not os.path.isfile(dst):
        logging.info("installing kubectl")
        sp.call(install_cmds[os_platform], shell=True)
    else:
        logging.info("kubectl already installed in {0}".format(dst))


def install_helm(os_platform):
    """Installs Kubernetes Helm"""
    install_cmds = {
        'Darwin': 'curl -LO https://storage.googleapis.com/kubernetes-helm/helm-v2.6.1-darwin-amd64.tar.gz && \
        tar zvxf helm-v2.6.1-darwin-amd64.tar.gz --strip-components=1 darwin-amd64/helm && \
        chmod +x helm && \
        mv helm /usr/local/bin/ && \
        rm helm-v2.6.1-darwin-amd64.tar.gz'
    }
    dst = '/usr/local/bin/helm'
    if not os.path.isfile(dst):
        logging.info("installing helm")
        sp.call(install_cmds[os_platform], shell=True)
    else:
        logging.info("helm already installed in {0}".format(dst))


def install_landscaper(os_platform):
    """Installs Helm Landscaper"""
    install_cmds = {
        'Darwin': 'curl -LO https://github.com/Eneco/landscaper/releases/download/1.0.10/landscaper-1.0.11-darwin-amd64.tar.gz && \
        tar zvxf landscaper-1.0.11-darwin-amd64.tar.gz landscaper && \
        mv landscaper /usr/local/bin/ && \
        rm landscaper-1.0.11-darwin-amd64.tar.gz'
    }
    dst = '/usr/local/bin/landscaper'
    if not os.path.isfile(dst):
        logging.info("installing landscaper")
        sp.call(install_cmds[os_platform], shell=True)
    else:
        logging.info("landscaper already installed in {0}".format(dst))


def install_terraform(os_platform):
    """Installs Terraform"""
    install_cmds = {
        'Darwin': 'curl -LO https://releases.hashicorp.com/terraform/0.10.2/terraform_0.10.7_darwin_amd64.zip && \
        unzip -d /usr/local/bin terraform_0.10.7_darwin_amd64.zip && \
        rm terraform_0.10.7_darwin_amd64.zip'
    }
    dst = '/usr/local/bin/terraform'
    if not os.path.isfile(dst):
        logging.info("installing terraform")
        sp.call(install_cmds[os_platform], shell=True)
    else:
        logging.info("terraform already installed in {0}".format(dst))


def install_helm_plugins():
    """Install helm plugins. Requires helm to be installed"""
    plugins = {
        'https://github.com/technosophos/helm-gpg': '0.1.0',
        'https://github.com/technosophos/helm-template': '2.4.1+2',
    }
    for plugin_url, version in plugins.items():
        install_cmd = "helm plugin install {0} --version={1}".format(
                                                    plugin_url,
                                                    version)
        logging.info("installing helm plugin with command: {0}".format(install_cmd))
        sp.call(install_cmd, shell=True)
