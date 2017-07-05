# -*- coding: utf-8 -*-
"""Various helper utilities"""

import subprocess

def namespace_exists(namespace):
    if subprocess.call(['kubectl', 'get', 'ns', namespace], shell=True):
        return True
    else:
        return False
	

def kubernetes_get_context():
    k8s_get_context_cmd = "kubectl config current-context"
    proc = subprocess.Popen(k8s_get_context_cmd, stdout=subprocess.PIPE, shell=True)
    k8s_context = proc.stdout.read().rstrip()
    return k8s_context


def git_get_branch():
	return subprocess.check_output(['git', 'symbolic-ref', 'HEAD', '--short' ]).rstrip()


def kubernetes_set_context(k8s_context):
    if subprocess.call(['kubectl', 'config', 'use-context', k8s_context], shell=True):
        return True
    else:
        return False
