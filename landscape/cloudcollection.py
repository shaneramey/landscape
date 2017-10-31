from .vault import VaultClient
from .cloud_minikube import MinikubeCloud
from .cloud_terraform import TerraformCloud
from .cloud_unmanaged import UnmanagedCloud

class CloudCollection(object):
    def __init__(self, cloud_provisioner, tf_root):
        """Fetches rows from a Bigtable.

        Retrieves rows pertaining to the given keys from the Table instance
        represented by big_table.  Silly things may happen if
        other_silly_variable is not None.

        Args:
            big_table: An open Bigtable Table instance.
            keys: A sequence of strings representing the key of each table row
                to fetch.
            other_silly_variable: Another optional variable, that has a much
                longer name than the other args, and which does nothing.

        Returns:
            A dict mapping keys to the corresponding table row data
            fetched. Each row is represented as a tuple of strings. For
            example:

            {'Serak': ('Rigel VII', 'Preparer'),
             'Zim': ('Irk', 'Invader'),
             'Lrrr': ('Omicron Persei 8', 'Emperor')}

            If a key from the keys argument is missing from the dictionary,
            then that row was not found in the table.

        Raises:
            IOError: An error occurred accessing the bigtable.Table object.
        """
        self.__provisioner = cloud_provisioner
        self.tf_root = tf_root

    def __str__(self):
        """Pretty-prints a list of clusters

        Args:
            self: the current object

        Returns:
            A new-line separated str of cluster names

        Raises:
            None.
        """

        return '\n'.join(self.__clouds.keys())


    def __getitem__(self, cloud_name):
        """Enables CloudCollection to be subscriptable.

        Used to iterate and index clouds

        Usage:
            cc = CloudCollection()
            cc['minikube'] is a MinikubeCloud object

        Args:
            cloud_name: The unique name of the cloud. GCE uses Project ID

        Returns:
            A Cloud object.

        Raises:
            None.
        """
        retval = self.list()[cloud_name]
        return retval


    def list(self):
        """Retrieves all clouds from Vault

        Args:
            None.

        Returns:
            A dict of clouds, having their unique identifier as a key
            fetched. Each row is represented as a tuple of strings. For
            example:

            {'minikube': <MinikubeCloud>}

        Raises:
            ValueError: if Vault doesn't understand the cloud provisioner
        """
        vault_cloud_prefix = '/secret/landscape/clouds'
        vc = VaultClient()
        clouds_in_vault = vc.dump_vault_from_prefix(vault_cloud_prefix, strip_root_key=True)
        cloud_db = {}
        for cloud_id in clouds_in_vault.keys():
            cloud_parameters = clouds_in_vault[cloud_id]
            cloud_in_vault_provisioner = cloud_parameters['provisioner']
            if cloud_in_vault_provisioner == self.__provisioner or self.__provisioner is None:
                cloud_parameters.update({'name': cloud_id})
                if cloud_in_vault_provisioner == 'minikube':
                    cloud_db[cloud_id] = MinikubeCloud(**cloud_parameters)
                elif cloud_in_vault_provisioner == 'terraform':
                    cloud_parameters.update({'terraform_templates_dir': self.tf_root})
                    cloud_db[cloud_id] = TerraformCloud(**cloud_parameters)
                elif cloud_in_vault_provisioner == 'unmanaged':
                    cloud_db[cloud_id] = UnmanagedCloud(**cloud_parameters)
                else:
                    raise ValueError("Unknown provisioner found in Vault: {0}".format(cloud_in_vault_provisioner))
        return cloud_db
