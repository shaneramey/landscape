import hvac
import os
import sys
import yaml
import base64

def kubeconfig_context_entry(context_name):
    """
    Generates a kubeconfig context entry

    Arguments:
     - context_name (str): The Kubernetes context

    Returns: context entry for kubeconfig file (dict)
    """
    context_entry = {
        'name': context_name,
        'context': {
            'cluster': context_name + '-cluster',
            'user': context_name + '-user',
        }
    }
    return context_entry


def kubeconfig_cluster_entry(context_name, k8s_server, ca_cert):
    """
    Generates a kubeconfig cluster entry

    Arguments:
     - context_name (str): The Kubernetes context
     - k8s_server (str): The URL of the Kubernetes API server
     - client_key (str): The PEM-encoded CA certificate to verify against

    Returns: cluster entry for kubeconfig file (dict)
    """
    base64_ca_cert = base64.b64encode(bytes(ca_cert, 'utf-8')).decode('ascii')

    cluster_entry = {
        'name': context_name + '-cluster',
        'cluster': {
            'server': k8s_server,
            'certificate-authority-data': base64_ca_cert
        }
    }
    return cluster_entry


def kubeconfig_user_entry(context_name, client_cert, client_key):
    """
    Generates a kubeconfig user entry

    Arguments:
     - context_name (str): The Kubernetes context
     - client_cert (str): The PEM-encoded client cert
     - client_key (str): The PEM-encoded client key

    Returns: user entry for kubeconfig file (dict)
    """
    base64_cert = base64.b64encode(bytes(client_cert, 'utf-8')).decode('ascii')
    base64_key = base64.b64encode(bytes(client_key, 'utf-8')).decode('ascii')

    user_entry = {
        'name': context_name + '-user',
        'user': {
            'client-certificate-data': base64_cert,
            'client-key-data': base64_key
        }
    }
    return user_entry


def write_kubeconfig(cfg_path):
    """
    Writes a kubernetes client configuration file with values from Vault

    Expects Vault to be pre-populated like so:
    
    vault write /secret/k8s_contexts/minikube \
        ca_cert='ca_cert_value' \
        client_cert='client_cert_value' \
        client_key='client_key_value' \
        api_server='https://kubernetes.default.svc.cluster.local'
    
    Arguments:
     - cfg_path (str): Path to the kubeconfig file being written

    Returns: None
    """
    vault_root = '/secret/k8s_contexts'
    vault_addr = os.environ.get('VAULT_ADDR')
    vault_cacert = os.environ.get('VAULT_CACERT')
    vault_token = os.environ.get('VAULT_TOKEN')
    vault_client = hvac.Client(url=vault_addr,
                                token=vault_token,
                                verify=vault_cacert)

    k8sconfig_contents = {}
    for context in vault_client.list(vault_root)['data']['keys']:
        clustercfg_root = vault_root + '/' + context
        print("Reading kubeconfig settings from {0}".format(clustercfg_root))
        try:
            vault_clustercfg = vault_client.read(clustercfg_root)
        except hvac.exceptions.InvalidRequest:
            sys.exit("Failed to read from Vault. Check VAULT_ vars")

        if not vault_clustercfg:
            sys.exit("No entry {0} found in Vault path {1}".format(context,
                                                                    vault_root))

        vault_data = vault_clustercfg['data']

        server_addr = vault_data['api_server']
        server_cacert = vault_data['ca_cert']
        client_cert = vault_data['client_cert']
        client_key = vault_data['client_key']

        context_contents = gen_k8sconf(k8s_context=context,
                                api_server=server_addr,
                                ca_cert=server_cacert,
                                client_auth_cert=client_cert,
                                client_auth_key=client_key)
        k8sconfig_contents.update(context_contents)
    expanded_cfg_path = os.path.expanduser(cfg_path)
    cfg_dir = '/'.join(expanded_cfg_path.split('/')[0:-1])
    if not os.path.exists(cfg_dir):
        print("Creating directory {0}".format(cfg_dir))
        os.makedirs(cfg_dir)
    with open(expanded_cfg_path, 'w') as kubeconfig:
        kubeconfig.write(yaml.dump(k8sconfig_contents,default_flow_style=False))
        print("Wrote kubeconfig to {0}".format(expanded_cfg_path))


def gen_k8sconf(k8s_context=None, api_server=None, ca_cert=None,
                client_auth_cert=None,
                client_auth_key=None):
    """
    Generate a kubeconfig object

    Arguments:
     - k8s_context (str):
     - api_server (str):
     - ca_cert (str):
     - client_auth_cert (str):
     - client_auth_key (str):

    Returns: kubeconfig data (dict)
    """
    contents = {}
    contents['apiVersion'] = 'v1'
    contents['kind'] = 'Config'
    contents['preferences'] = {}
    contents['clusters'] = []
    contents['contexts'] = []
    contents['users'] = []
    contents['current-context'] = k8s_context

    vault_context_entry = kubeconfig_context_entry(k8s_context)
    vault_cluster_entry = kubeconfig_cluster_entry(k8s_context,
                                                    api_server,
                                                    ca_cert)
    vault_user_entry = kubeconfig_user_entry(k8s_context,
                                                client_auth_cert,
                                                client_auth_key)
    contents['contexts'].append(vault_context_entry)
    contents['clusters'].append(vault_cluster_entry)
    contents['users'].append(vault_user_entry)

    return contents


def read_kubeconfig(cfg_path):
    """
    Reads the current kubeconfig file and places it into Vault
    """
    k8sconfig_contents = {}
    with open(cfg_path, 'r') as stream:
        try:
            k8sconfig_contents = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    contexts = k8sconfig_contents['contexts']
    clusters = k8sconfig_contents['clusters']
    users = k8sconfig_contents['users']

    for context in contexts:
        # kubeconfig context entries
        context_name = context['name']
        # gke clusters are set with GOOGLE_CREDENTIALS, not here
        if context_name.startswith('gke_'):
            continue
        context_cluster = context['context']['cluster']
        context_user = context['context']['user']
        # kubeconfig cluster entries
        cluster_cacert = ''
        client_auth_cert = ''
        client_auth_key = ''
        cluster_cfg = [d for d in clusters if d['name'] == context_cluster][0]
        cluster_server = cluster_cfg['cluster']['server']
        if 'certificate-authority-data' in cluster_cfg['cluster']:
            ca_cert_data = cluster_cfg['cluster']['certificate-authority-data']
            cluster_cacert = base64.b64encode(bytes(ca_cert_data, 'utf-8')).decode('ascii')
        elif 'certificate-authority' in cluster_cfg['cluster']:
            cacert_file = cluster_cfg['cluster']['certificate-authority']
            if cacert_file.startswith('/'):
                cacert_path = cacert_file
            else:
                cacert_path = os.path.expanduser('~/.kube/' + cacert_file)
            with open(cacert_path, 'r') as stream:
                try:
                    cluster_cacert = yaml.load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
        else:
            raise "no user certificate-authority(-data) entry in kubeconfig"
        # kubeconfig user entries
        user_cfg = [d for d in users if d['name'] == context_user][0]
        print("user_cfg={0}".format(user_cfg))
        if 'client-certificate-data' in user_cfg['user']:
            client_cert_data = user_cfg['user']['client-certificate-data']
            client_key_data = user_cfg['user']['client-key-data']
            client_auth_cert = base64.b64encode(bytes(client_cert_data, 'utf-8')).decode('ascii')
            client_auth_key = base64.b64encode(bytes(client_key_data, 'utf-8')).decode('ascii')
        elif 'client-certificate' in user_cfg['user']:
            client_cert_file = user_cfg['user']['client-certificate']
            client_key_file = user_cfg['user']['client-key']
            # client cert
            if client_cert_file.startswith('/'):
                client_cert_path = client_cert_file
            else:
                client_cert_path = os.path.expanduser('~/.kube/' + client_cert_file)
            with open(client_cert_path, 'r') as stream:
                try:
                    client_auth_cert = yaml.load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
            # client key
            if client_key_file.startswith('/'):
                client_key_path = client_key_file
            else:
                client_key_path = os.path.expanduser('~/.kube/' + client_key_file)
            with open(client_key_path, 'r') as stream:
                try:
                    client_auth_key = yaml.load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
        print("client_auth_cert={0}".format(client_auth_cert))
        print("client_auth_key={0}".format(client_auth_key))

    raise "read_kubeconfig not implemented"


class VaultClient(object):
    def __init__(self):
        vault_addr = os.environ.get('VAULT_ADDR')
        vault_cacert = os.environ.get('VAULT_CACERT')
        vault_token = os.environ.get('VAULT_TOKEN')

        # Raise error if VAUT_ environment variables not set
        missing_fmt_string = '{0} missing in environment'
        if not vault_addr:
            raise ValueError(missing_fmt_string.format('VAULT_ADDR'))
        if not vault_token:
            raise ValueError(missing_fmt_string.format('VAULT_TOKEN'))
        if vault_addr.startswith('https://') and not vault_cacert:
            raise ValueError(missing_fmt_string.format('VAULT_CACERT'))

        self.__vault_client = hvac.Client(url=vault_addr,
                                    token=vault_token,
                                    verify=vault_cacert)


    def dump_vault_from_prefix(self, path_prefix, strip_root_key=False):
        """
        Dump Vault data at prefix into dict

        Arguments:
         - path_prefix (str): The prefix which to dump
         - strip_root_key (bool): Strip the root key from return value

        Returns: data from Vault at prefix (dict)
        """
        all_values_at_prefix = {}
        print(" - reading vault subkeys at {0}".format(path_prefix))
        subkeys_at_prefix = self.__vault_client.list(path_prefix)

        # use last vault key (delimited by '/') as dict index
        prefix_keyname = path_prefix.split('/')[-1]
        if not prefix_keyname in all_values_at_prefix:
            all_values_at_prefix[prefix_keyname] = {}

        if subkeys_at_prefix:
            for subkey in subkeys_at_prefix['data']['keys']:
                prefixed_key = path_prefix + '/' + subkey
                all_values_at_prefix[prefix_keyname].update(self.dump_vault_from_prefix(prefixed_key))
        else:
            all_values_at_prefix[prefix_keyname].update(self.__vault_client.read(path_prefix)['data'])
        if strip_root_key == True:
            retval = all_values_at_prefix[prefix_keyname]
        else:
            retval = all_values_at_prefix
        return retval
