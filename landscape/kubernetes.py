import subprocess 

def kubernetes_get_context():
    k8s_get_context_cmd = "kubectl config current-context"
    proc = subprocess.Popen(k8s_get_context_cmd, stdout=subprocess.PIPE, shell=True)
    k8s_context = proc.stdout.read().rstrip()
    return k8s_context


def kubernetes_set_context(k8s_context):
    set_context_cmd = "kubectl config use-context {0}".format(k8s_context)
    if subprocess.call(set_context_cmd, shell=True):
        return True
    else:
        return False
