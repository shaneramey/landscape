import subprocess
import sys
import os
import logging

from .cloud import Cloud

class TerraformCloud(Cloud):
    """A Terraform-provisioned resource-set

    Secrets path must exist as:
    vault write /secret/landscape/clouds/staging-123456 provisioner=terraform \
        google_credentials=

    Attributes:
        tf_templates_dir: String containing path to terraform templates
        gce_creds: GOOGLE_APPICATION_CREDENTIALS for cloud
        terraform_dir: String containing path to terraform templates (TODO: dup)

        Other attributes inherited from superclass.

    """

    def __init__(self, **kwargs):
        """Initializes an instance of TerraformCloud

        Args:
            kwargs**:
                name: The GCE Project ID

        Returns:
            A string containing the Cloud ID, pulled from Vault.

        Raises:
            None.
        """
        Cloud.__init__(self, **kwargs)
        self.terraform_dir = os.getcwd() + '/terraform-templates'
        self.terraform_statefile = self.terraform_dir + '/.terraform/terraform.' + self.name + '.tfstate'
        self.gce_creds = kwargs['google_credentials']
        self.__gcp_auth_jsonfile = os.getcwd() + '/cloud-serviceaccount-' + self.name + '.json'
        self.write_gcloud_keyfile_json()
        logging.debug("Using Terraform Directory: " + self.terraform_dir)


    def envvars(self):
        """Updates current environment variables for Google and Terraform.

        Sets GOOGLE_APPLICATION_CREDENTIALS for interacting with GCP
        Sets TF_LOG for log verbosity

        Args:
            None.

        Returns:
            A combined dict of original + injected environment variables.

        Raises:
            None.
        """
        current_log_level_int = logging.getLogger().getEffectiveLevel()
        current_log_level = logging.getLevelName(current_log_level_int)
        tf_log = 'INFO'
        if current_log_level == 'DEBUG':
            tf_log = 'TRACE'
        return os.environ.update({
            'GOOGLE_APPLICATION_CREDENTIALS': self.__gcp_auth_jsonfile,
            'TF_LOG': tf_log
        })


    def service_account_email(self):
        """The email address for GCP's GOOGLE_APPLICATION_CREDENTIALS

        Args:
            None.

        Returns:
            A string containing the authenticated GCP email address.

        Raises:
            None.
        """
        gce_creds = json.loads(self.gce_creds)
        return gce_creds['client_email']


    def write_gcloud_keyfile_json(self):
        google_application_creds_file = self.__gcp_auth_jsonfile
        logging.debug("Writing GOOGLE_APPLICATION_CREDENTIALS to {0}".format(google_application_creds_file))
        f = open(google_application_creds_file, "w")
        f = open(self.__gcp_auth_jsonfile, "w")
        f.write(self.gce_creds)
        f.close()


    def converge(self, dry_run):
        """Converges a Terraform cloud environment.

        Checks if a terraform cloud is already running
        Initializes it if not yet running

        Args:
            dry_run: flag for simulating convergence

        Returns:
            None.

        Raises:
            None.
        """
        self.init_terraform(dry_run)

        # Generate terraform command: populate variables
        tf_vars_args = '-var="gce_project_id={0}" ' + \
                        '-var="gke_cluster1_name={1}" ' + \
                        '-var="gke_cluster1_version={2}"'
        terraform_vars = tf_vars_args.format(self.name,
                            'master',
                            '1.8.1-gke.0')
        # Generate terraform command: dry-run
        terraform_cmd_tmpl = 'terraform validate ' + terraform_vars + \
            ' && ' + \
            'terraform plan ' + terraform_vars + \
            " -state={0}".format(self.terraform_statefile)

        if not dry_run:
            terraform_cmd_tmpl += ' && terraform apply ' + terraform_vars + \
                                    " -state={0}".format(self.terraform_statefile)
        terraform_cmd = terraform_cmd_tmpl.format(self.name,
                                                    'master',
                                                    '1.8.1-gke.0')
        if not dry_run:
            logging.info('  - applying terraform state with command: ' + terraform_cmd)
            failed_to_apply_terraform = subprocess.call(terraform_cmd,
                                                        cwd=self.terraform_dir,
                                                        env=self.envvars(),
                                                        shell=True)
            if failed_to_apply_terraform:
                sys.exit('ERROR: terraform command failed')
        else:
            logging.info("DRYRUN: would be Converging terraform with command: {0} in directory: {1}".format(terraform_cmd, self.terraform_dir))



    def init_terraform(self, dry_run):
        """Initializes a terraform cloud.

        Args:
            dry_run: flag for simulating convergence

        Returns:
            None.        

        Raises:
            None.        
        """
        self.link_terraform_state_to_project()

        tf_init_cmd_tmpl = 'terraform init ' + \
                        '-backend-config "bucket=tfstate-{0}" ' + \
                        '-backend-config "path=tfstate-{0}" ' + \
                        '-backend-config "project={0}" '

        tf_init_cmd = tf_init_cmd_tmpl.format(self.name)

        if not dry_run:
            logging.info('Initializing terraform: ' + tf_init_cmd)
            failed_to_init_terraform = subprocess.call(tf_init_cmd,
                                                    cwd=self.terraform_dir,
                                                    env=self.envvars(),
                                                    shell=True)
            if failed_to_init_terraform:
                sys.exit('ERROR: terraform init failed')
        else:
            logging.info("DRYRUN: would be Initializing terraform with command: {0} in directory: {1}".format(tf_init_cmd, self.terraform_dir))


    def link_terraform_state_to_project(self):
        """Links terraform.tfstate to terraform.${project_id}.tfstate

        Works around the inability for Terraform to support environments in GCS
        until https://github.com/hashicorp/terraform/issues/14909 is resolved.
        Can only operate on one terraform environment at a time.

        Args:
            None.        

        Returns:
            None.        

        Raises:
            None.        
        """

        # https://github.com/pll/terraform_infrastructure/blob/118152322c782dab684c05dbf38c7a0f3c5965f5/runTF.py#L105
        # cd .terraform
        # touch terraform.prod-165617.tfstate
        # ln -s terraform.prod-165617.tfstate terraform.tfstate

        symlink_to_manage = self.terraform_dir + '/.terraform/terraform.tfstate'
        project_terraform_statefile = self.terraform_statefile
        logging.info("Attempting to link {0} to {1}".format(project_terraform_statefile, symlink_to_manage))

        if os.path.exists(symlink_to_manage):
            # Yes, but is it a symlink?
            if os.path.islink(symlink_to_manage):
                # Yes, but is it pointing to the correct place?
                if os.readlink(symlink_to_manage) != project_terraform_statefile:
                    # No, so unlink it and re-link to my VPC state.
                    os.unlink(symlink_to_manage)
                    os.symlink(project_terraform_statefile, symlink_to_manage)
            # It's not a symlink, so let's rename .terraform/terraform.tfstate
            # to .terraform/terraform-${project_id}.tfstate and link it back
            else:
                os.rename(symlink_to_manage, project_terraform_statefile)
                os.symlink(project_terraform_statefile, symlink_to_manage)
