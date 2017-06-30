# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
"""Deploy Kubernetes clusters and apply Landscaper / Helm configurations."""
__title__ = 'landscape'
__author__ = 'Shane Ramey'
__license__ = 'Apache 2.0'
__version__ = '0.0.1'
__copyright__ = 'Copyright 2017'

DEFAULT_OPTIONS = {
    'DEFAULT': {
        'lastpass_folder': '',
    },
    'lastpass': {
        'folder': 'Shared-k8s/k8s-landscaper',
    },
    'minikube': {
    	'init_cmd_template': 'minikube start \
                    --vm-driver={0} \
                    --dns-domain={1} \
                    --kubernetes-version=v1.6.4 \
                    --extra-config=apiserver.Authorization.Mode=RBAC \
                    --extra-config=controller-manager.ClusterSigningCertFile=/var/lib/localkube/certs/ca.crt \
                    --extra-config=controller-manager.ClusterSigningKeyFile=/var/lib/localkube/certs/ca.key \
                    --cpus=8 \
                    --disk-size=20g \
                    --memory=8192 \
                    -v=0'
    },
}
