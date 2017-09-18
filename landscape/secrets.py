import subprocess
import sys


class UniversalSecrets(object):
    def __init__(self, **kwargs):
    	self.__provider = kwargs['provider']


    def __str__(self):
        return str(self.__clouds)


    def __getitem__(self, cloud_name):
        retval = self.__clouds[cloud_name]
        return retval

    def overwrite_vault(self, shared_secrets_folder):
        pull_secrets_cmd = 'lpass show {} --notes'.format(shared_secrets_folder)
        pull_secrets_failed = subprocess.call(pull_secrets_cmd, shell=True)
        if pull_secrets_failed:
            sys.exit("ERROR: non-zero retval for {}".format(pull_secrets_failed))
