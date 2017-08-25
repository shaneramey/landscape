import subprocess
import sys
import os

from .cloud import Cloud

class TerraformCloud(Cloud):
    """
    vault write /secret/landscape/clouds/staging-165617 provisioner=terraform \
        google_credentials=
    """
    def __init__(self, **kwargs):
        Cloud.__init__(self, **kwargs)
        self.tf_templates_dir = '.'
        self.gce_creds = kwargs['google_credentials']


    @property
    def gce_project(self):
        return self.name


    @property
    def terraform_dir(self):
        return self.tf_templates_dir


    @terraform_dir.setter
    def terraform_dir(self, template_dir):
        self.tf_templates_dir = template_dir


    def envvars(self):
        return os.environ.update({
            'GOOGLE_CREDENTIALS': self.gce_creds,
            'TF_LOG': 'DEBUG'
        })


    def tf_varstr(self):
        tf_vars_args  = '-var="gce_project_id={0}" ' + \
                        '-var="gke_cluster1_name={1}" ' + \
                        '-var="gke_cluster1_version={2}"'
        return tf_vars_args.format(self.gce_project,
                                    'master',
                                    '1.7.0')
    def converge(self):
        """
        Checks if a terraform cloud is already running
        Initializes it if not yet running

        Returns: None

        """
        self.init_terraform()
        terraform_cmd_tmpl = 'terraform validate ' + self.tf_varstr() + \
            ' && ' + \
            'terraform plan ' + self.tf_varstr() + \
            ' && ' + \
            'terraform apply ' + self.tf_varstr()

        terraform_cmd = terraform_cmd_tmpl.format(self.gce_project,
                                                    'master',
                                                    '1.7.0')
        print('  - applying terraform state with command: ' + terraform_cmd)
        failed_to_apply_terraform = subprocess.call(terraform_cmd,
                                                    cwd=self.terraform_dir,
                                                    env=self.envvars(),
                                                    shell=True)
        if failed_to_apply_terraform:
            sys.exit('ERROR: terraform command failed')


    def init_terraform(self):
        """
        initializes a terraform cloud
        """
        tf_init_cmd_tmpl = 'terraform init ' + \
                        '-backend-config "bucket=tfstate-{0}" ' + \
                        '-backend-config "path=tfstate-{0}" ' + \
                        '-backend-config "project={0}"'

        tf_init_cmd = tf_init_cmd_tmpl.format(self.gce_project)

        print('  - initializing terraform with command: ' + tf_init_cmd)
        failed_to_init_terraform = subprocess.call(tf_init_cmd,
                                                    cwd=self.terraform_dir,
                                                    env=self.envvars(),
                                                    shell=True)
        if failed_to_init_terraform:
            sys.exit('ERROR: terraform init failed')
