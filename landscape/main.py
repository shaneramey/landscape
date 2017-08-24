#! /usr/bin/env python3

"""
landscape: Provisions Kubernetes clusters and Helm charts, with secrets in Hashicorp Vault

Usage:
  landscape cloud list [--provisioner=<cloud_provisioner>]
  landscape cloud converge [--cloud=<cloud_project>]
  landscape cluster list [--provisioner=<cloud_provisioner>]
  landscape cluster converge --context=<cluster_name> 
      [--provisioner=<provisioner>]
      [--gce-project-id=<gce_project_id>] [--minikube-driver=<driver>]
      [--kubernetes-version=<k8s_version>] [--cluster-dns-domain=<dns_domain>]
      [--landscaper-git-branch=<git_branch>]
      [--tf-templates-dir=<tf_templates_dir> ] [--debug]
      [--switch-to-cluster-context=<boolean>]
  landscape cluster environment (--write-kubeconfig|--read-kubeconfig) [--kubeconfig-file=<kubecfg>]
  landscape charts converge --context=<context_name>
      [--namespace=<namespace>] [--chart=<chart_name>]
  landscape tools install

Options:
  --context=<context_name>                     Operate on context, defined in Vault
  --write-kubeconfig                           Write ~/.kube/config with contents from Vault
  --read-kubeconfig                           Read ~/.kube/config and put its contents in Vault
  --kubeconfig-file=<kubecfg>                  Specify path to KUBECONFIG [default: ~/.kube/config-landscaper].
  --cloud=<cloud_project>                      k8s cloud provisioner.
  --project=<gce_project_id>                   in GCE environment, which project ID to use. [default: minikube].
  --kubernetes-version=<k8s_version>           in GCE environment, which project ID to use [default: 1.7.0].
  --cluster-dns-domain=<dns_domain>            DNS domain used for inside-cluster DNS [default: cluster.local].
  --minikube-driver=<driver>                   (minikube only) driver type (virtualbox|xhyve) [default: virtualbox].
  --switch-to-cluster-context=<boolean>        switch to kubernetes context after cluster converges [default: true].
  --namespace=<namespace>                      install only charts under specified namespace.
  --fetch-lastpass                             Fetches values from Lastpass and puts them in Vault
  --tf-templates-dir=<tf_templates_dir>        Terraform templates directory [default: ./tf-templates].
  --debug                                      Run in debug mode.
Provisioner can be one of minikube, terraform.
"""

import docopt
import os

from .cloudcollection import CloudCollection
from .cluster import LandscapeCluster
from .minikube import MinikubeCluster
from .terraform import TerraformCluster
from .charts import HelmChartSet
from .client import kubectl_use_context
from .kubernetes import kubernetes_get_context
from .vault import (read_kubeconfig, write_kubeconfig)
from .tools import install_tools

def main():
    clouds = CloudCollection()
    # branch is used to pull secrets from Vault, and to distinguish clusters
    args = docopt.docopt(__doc__)
    provisioner = args['--provisioner']
    # landscape cloud list
    if args['cloud'] and args['list']:
        for cloud_name in clouds.list(provisioner):
            print(cloud_name)
    # landscape cloud converge
    elif args['cloud'] and args['converge']:
        cloud_selection = args['--cloud']
        # terraform_templates_dir
        #
        clouds[cloud_selection].terraform_dir = args['--tf-templates-dir']
        clouds[cloud_selection].converge()
    elif args['cluster']:
        context_in_vault = args['--context']
        # landscape cluster list
        if args['list']:
            targets = LandscapeCluster.list_clusters()
            for target in targets:
              print(target)
        # landscape cluster environment
        if args['environment']:
            kubecfg_file = args['--kubeconfig-file']
            if args['--write-kubeconfig']:
                write_kubeconfig(cfg_path=kubecfg_file)
            if args['--read-kubeconfig']:
                read_kubeconfig(cfg_path=kubecfg_file)
        elif args['converge']:
            # common to all cluster types
            k8s_version = args['--kubernetes-version']

            if provisioner == 'minikube':
                driver = args['--minikube-driver']
                cluster_dns_domain = args['--cluster-dns-domain']
                cluster = MinikubeCluster(k8s_version, driver, cluster_dns_domain)
                cluster.converge()
            elif provisioner == 'terraform':
                gce_project_id = args['--gce-project-id']
                tf_templates_dir = args['--tf-templates-dir']
                debug_flag = args['--debug']
                print("args={0}".format(args))
                cluster = TerraformCluster(k8s_version, gce_project_id,
                                            tf_templates_dir, debug_flag)
                cluster.converge()
                # switch local kubectl to use cluster context
                if args['--switch-to-cluster-context'] == 'true':
                    kubectl_use_context(cluster.kubeconfig_context_name)
    # landscape charts
    elif args['charts']:
        if args['--namespace'] is not None:
            namespaces = args['--namespace'].split(',')
        else:
            namespaces = None

        kubecontext = args['--context']
        if not kubecontext:
            kubecontext = kubernetes_get_context()
        print("Using Kubernetes context {0}".format(kubecontext))
        chart_set = HelmChartSet('.', kubecontext, namespaces)
        chart_set.converge()
    # landscape charts
    elif args['tools'] and args['install']:
        install_tools()

if __name__ == "__main__":
    main()
