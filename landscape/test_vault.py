from .vault import kubeconfig_context_entry

def test_kubeconfig_context_entry_minikube():
	mock_context_entry = {
        'name': 'minikube',
        'context': {
            'cluster': 'minikube-cluster',
            'user': 'minikube-user',
        }
    }
	assert kubeconfig_context_entry('minikube') == mock_context_entry
