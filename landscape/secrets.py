import subprocess
import sys


class UniversalSecrets(object):
    def __init__(self, **kwargs):
    	self.__provider = kwargs['provider']


    def __str__(self):
        return str(self.__secrets)


    def __getitem__(self, secret_name):
        retval = self.__secrets[secret_name]
        return retval

    def overwrite_vault(self, shared_secrets_folder):
        pull_secrets_cmd = 'lpass show {} --notes'.format(shared_secrets_folder)
        print("Running {0}".format(pull_secrets_cmd))
        proc = subprocess.Popen(pull_secrets_cmd, stdout=subprocess.PIPE, shell=True)
        secrets_write_commands_from_lastpass = proc.stdout.read().rstrip().decode()
        # wait for command return code
        proc.communicate()[0]
        if proc.returncode != 0:
            raise ChildProcessError('Could not read LastPass secrets')
        write_secrets_to_vault_failed = subprocess.call(secrets_write_commands_from_lastpass, shell=True)
        if write_secrets_to_vault_failed:
            sys.exit("ERROR: non-zero retval for {}".format(write_secrets_to_vault_failed))