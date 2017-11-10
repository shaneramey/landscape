import logging

from .vault import VaultClient
from .cloud_minikube import MinikubeCloud
from .cloud_terraform import TerraformCloud
from .cloud_unmanaged import UnmanagedCloud

class CloudCollection(object):
    """A group of clouds.

    Generates a list of clouds. Cluster type is determined by its Cloud's
    "provisioner" attribute. Each cloud behaves differently
    (i.e., provision VMs) based on its type

    Attributes:
        clouds: (optionally) filtered list of clouds, read from Vault
    """

    def __init__(self, charts_git_branch_selector=''):
        """initializes a CloudCollection for a given git branch.

        Reads a dict of clouds from Vault, and filter the results based on the
        git branch passed into the constructor.

        Args:
            charts_git_branch_selector(str): If set, CloudCollection is
                composed of only clouds subscribed to this branch. Set in
                Vault-defined settings for the cloud

        Returns:
            None.

        Raises:
            None.
        """

        self.charts_git_branch_selector = charts_git_branch_selector
        self.clouds = self.__filter_clouds(charts_git_branch_selector)


    def __str__(self):
        """Pretty-prints a list of clouds

        Args:
            self: the current object

        Returns:
            A new-line separated str of cloud names

        Raises:
            None.
        """
        cloud_names = []
        for cloud in self.clouds:
            cloud_names.append(cloud.name)
        return '\n'.join(cloud_names)


    def __getitem__(self, cloud_name):
        """returns a Cloud with a given name.

        Used to iterate and index clouds

        Args:
            cloud_name: index for the cloud within self.clusters

        Returns:
            A single Cloud object named cloud_name.

        Raises:
            None.
        """
        logging.debug("cloud_name is".format(cloud_name))
        logging.debug("clouds are".format(self.clouds))
        cloud = next((item for item in self.clouds if item.name == cloud_name))
        return cloud


    def __filter_clouds(self, charts_branch_selection):
        """Loads clouds from Vault and filters them
        """
        vault_clouds = self.__load_clouds_from_vault()
        filtered_clouds = []
        # Look at each Vault key's name for its context
        for vault_cloud in vault_clouds:
            # If charts_git_branch_selector is None, generate collection of
            # all clouds. Otherwise, generate collection including only
            # clouds subscribing to this branch.
            if charts_branch_selection == vault_cloud.git_branch or \
                not charts_branch_selection:
                filtered_clouds.append(vault_cloud)

        return filtered_clouds


    def __load_clouds_from_vault(self):
        """Retrieves cloud definitions from Vault and loads them into a dict

        Args:
            None.

        Returns:
            A dict mapping keys to the corresponding table row data
            fetched. Each row is represented as a tuple of strings. For
            example:

            {
                'staging-123456': <TerraformCloud>,
                'minikube': <MinikubeCloud>
            }

        Raises:
            None.
        """
        vault_cloud_prefix = '/secret/landscape/clouds'
        # Dump Vault
        cloud_defs = VaultClient().dump_vault_from_prefix(
            vault_cloud_prefix, strip_root_key=True)
        clouds = []
        for cloud_name in cloud_defs:
            # inject cloud name into data
            cloud_def = cloud_defs[cloud_name]
            cloud_provisioner = cloud_def['provisioner']
            cloud_def.update({'name': cloud_name})
            if cloud_provisioner == 'minikube':
                clouds.append(MinikubeCloud(**cloud_def))
            elif cloud_provisioner == 'terraform':
                clouds.append(TerraformCloud(**cloud_def))
            elif cloud_provisioner == 'unmanaged':
                clouds.append(UnmanagedCloud(**cloud_def))
            else:
                raise ValueError("Unknown provisioner found in Vault: {0}".format(cloud_provisioner))
        return clouds


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

        return self.clouds
