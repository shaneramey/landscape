import subprocess
import sys
from .utils import test_dns_domain
from . import DEFAULT_OPTIONS

def apply_terraform_cluster(provisioner, dns_domain, project_id, template_dir, git_branch_name):
    """
    creates or converges a terraform-provisioned cluster to its desired-state

    Arguments:
     - provisioner: minikube or terraform
     - dns_domain: dns domain to use for cluster
                   In GKE environment, must be cluster.local
    Returns: None
    """
    print("project_id={0}".format(project_id))
    dns_check_succeeds = test_dns_domain(provisioner, dns_domain)
    if dns_check_succeeds:
        terraform_cmd_tmpl = DEFAULT_OPTIONS['terraform']['init_cmd_template']
        terraform_cmd = terraform_cmd_tmpl.format(project_id, git_branch_name)
        print('  - running ' + terraform_cmd)
        failed_to_apply_terraform = subprocess.call(terraform_cmd, cwd=template_dir, shell=True)
        if failed_to_apply_terraform:
            sys.exit('ERROR: terraform command failed')
    else:
        err_msg = "ERROR: DNS validation failed for {}".format(dns_domain)
        sys.exit(err_msg)


