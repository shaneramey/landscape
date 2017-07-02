# -*- coding: utf-8 -*-
"""Deploy a cluster and its Helm charts"""
import subprocess as sp
import sys
import os

def deploy_helm_charts_for_namespace(namespace):
    print(
        "### \
        # Namespace: {} \
        ### \
        \
        Deploying into namespace {}".format(namespace))
    create_namespace_if_needed(namespace)


def create_namespace_if_needed(namespace):
    """
    Checks if namespace exists, and if it doesn't - create it
    """
    need_ns = sp.call("kubectl get ns {}".format(namespace), shell=True)
    if need_ns:
        create_failed = sp.call("kubectl create ns {}".format(namespace))
        if create_failed:
            sys.exit("ERROR: failed to create namespace {}".format(namespace))


def deploy_helm_charts():
    print("Deploying all charts")
    deploy_charts_dir('charts_core')
    deploy_charts_dir('charts_minikube')


def deploy_charts_dir(chart_dir):
    print("Deploying charts in {}".format(chart_dir))
    for core_chart_dir in os.listdir(os.getcwd() + '/' + chart_dir):
        landscaper_apply_dir(core_chart_dir)

def deploy_minikube_charts():
    print("Deploying minikube charts")

def landscaper_apply_dir(directory):
    current_context = kubernetes_get_context()
    ls_apply_cmd = "landscaper apply -v \
                            --context={0} \
                            --namespace={1} \
                            charts_core/{1}".format(
                                                    current_context,
                                                    directory
                                                 )
    print(ls_apply_cmd)
    create_failed = sp.call(ls_apply_cmd)
    if create_failed:
        sys.exit("ERROR: non-zero retval for {}".format(ls_apply_cmd))

def kubernetes_get_context():
    k8s_get_context_cmd = "/usr/local/bin/kubectl config current-context"
    proc = sp.Popen(k8s_get_context_cmd, stdout=sp.PIPE, shell=True)
    k8s_context = proc.stdout.read()
    return k8s_context
