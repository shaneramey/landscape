#! /usr/bin/env python3

"""
landscape: Provisions Kubernetes clusters and Helm charts, with secrets in Hashicorp Vault

Usage:
  landscape cluster list
  landscape cluster environment (--write-kubeconfig|--read-kubeconfig) [--kubeconfig-file=<kubecfg>]
  landscape cluster (create|converge) --context=<cluster_name> 
      [--provisioner=<provisioner>]
      [--gce-project-id=<gce_project_id>] [--minikube-driver=<driver>]
      [--kubernetes-version=<k8s_version>] [--cluster-dns-domain=<dns_domain>]
      [--landscaper-git-branch=<git_branch>]
      [--tf-templates-dir=<tf_templates_dir> ] [--debug]
      [--switch-to-cluster-context=<boolean>]
  landscape charts converge --context=<context_name>
      [--namespace=<namespace>] [--chart=<chart_name>]

Options:
  --context=<context_name>                     Operate on context, defined in Vault
  --write-kubeconfig                           Write ~/.kube/config with contents from Vault
  --read-kubeconfig                           Read ~/.kube/config and put its contents in Vault
  --kubeconfig-file=<kubecfg>                  Specify path to KUBECONFIG [default: ~/.kube/config-landscaper].
  --provisioner=<provisioner>                  k8s provisioner [default: minikube].
  --gce-project-id=<gce_project_id>            in GCE environment, which project ID to use
  --kubernetes-version=<k8s_version>           in GCE environment, which project ID to use [default: 1.7.0].
  --kubernetes-domain=<gce_project_id>         in GCE environment, which project ID to use
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

from .cluster import LandscapeCluster
from .minikube import MinikubeCluster
from .terraform import TerraformCluster
from .charts import HelmChartSet
from .client import kubectl_use_context
from .kubernetes import kubernetes_get_context
from .vault import (read_kubeconfig, write_kubeconfig)

def main():
    # branch is used to pull secrets from Vault, and to distinguish clusters
    args = docopt.docopt(__doc__)
    provisioner = args['--provisioner']
    if args['cluster']:
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
    if args['charts']:
        if args['--namespace'] is not None:
            namespaces = args['--namespace'].split(',')
        else:
            namespaces = None

        kubecontext = args['--context']
        if not kubecontext:
            kubecontext = kubernetes_get_context()
        print("kubecontext={0}".format(kubecontext))
        chart_set = HelmChartSet('.', kubecontext, namespaces)
        chart_set.converge()


if __name__ == "__main__":
    main()
