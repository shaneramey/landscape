import subprocess
import sys
import os
import logging

from .cloud import Cloud

logging.basicConfig(level=logging.DEBUG)

class TerraformCloud(Cloud):
    """
    vault write /secret/landscape/clouds/staging-123456 provisioner=terraform \
        google_credentials=
    """
    def __init__(self, **kwargs):
        Cloud.__init__(self, **kwargs)
        self.tf_templates_dir = '.'
        self.gce_creds = kwargs['google_credentials']
        self.terraform_dir = kwargs['terraform_templates_dir']
        self.gcloud_auth_jsonfile = os.getcwd() + '/cloud-serviceaccount-' + self.name + '.json'
        self.write_gcloud_keyfile_json()

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
            'GOOGLE_APPLICATION_CREDENTIALS': self.gcloud_auth_jsonfile,
            'TF_LOG': 'TRACE'
        })

    def service_account_email(self):
        gce_creds = json.loads(self.gce_creds)
        return gce_creds['client_email']


    def write_gcloud_keyfile_json(self):
        google_application_creds_file = self.gcloud_auth_jsonfile
        logging.debug("Writing GOOGLE_APPLICATION_CREDENTIALS to {0}".format(google_application_creds_file))
        f = open(google_application_creds_file, "w")
        f = open(self.gcloud_auth_jsonfile, "w")
        f.write(self.gce_creds)
        f.close()

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
        logging.info('  - applying terraform state with command: ' + terraform_cmd)
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

        logging.info('  - initializing terraform with command: ' + tf_init_cmd)
        failed_to_init_terraform = subprocess.call(tf_init_cmd,
                                                    cwd=self.terraform_dir,
                                                    env=self.envvars(),
                                                    shell=True)
        if failed_to_init_terraform:
            sys.exit('ERROR: terraform init failed')
