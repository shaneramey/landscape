import subprocess
import sys

def kubectl_use_context(context):
    set_context_cmd = "kubectl config use-context {0}".format(context)
    print(' - running ' + set_context_cmd)
    set_context_failed = subprocess.call(set_context_cmd, shell=True)
    if set_context_failed:
    	sys.exit('Error setting context. Exiting')

