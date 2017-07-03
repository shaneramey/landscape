# -*- coding: utf-8 -*-
"""Various helper utilities"""

import subprocess

def namespace_exists(namespace):
    if subprocess.call(['kubectl', 'get', 'ns', namespace], shell=True):
        return True
    else:
        return False
	
def kubernetes_get_context():
    k8s_get_context_cmd = "/usr/local/bin/kubectl config current-context"
    proc = subprocess.Popen(k8s_get_context_cmd, stdout=subprocess.PIPE, shell=True)
    k8s_context = proc.stdout.read().rstrip()
    return k8s_context