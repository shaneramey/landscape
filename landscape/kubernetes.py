import subprocess
import sys
import hvac

def kubernetes_get_context():
    """
    Retrieve current Kubernetes context

    Arguments: None

    Returns: Current Kubernetes context name (str)
    """
    get_context_cmd = "kubectl config current-context"
    print(' - running ' + get_context_cmd)
    proc = subprocess.Popen(get_context_cmd, stdout=subprocess.PIPE, shell=True)
    k8s_context = proc.stdout.read().rstrip().decode()
    return k8s_context


def kubectl_use_context(context):
    set_context_cmd = "kubectl config use-context {0}".format(context)
    print(' - running ' + set_context_cmd)
    set_context_failed = subprocess.call(set_context_cmd, shell=True)
    if set_context_failed:
    	sys.exit('Error setting context. Exiting')


def provisioner_from_context_name(context):
    if context == 'minikube':
        return 'minikube'
    elif context.startswith('gke_'):
        return 'terraform'
    else:
        sys.exit("Please pass minikube or terraform")

