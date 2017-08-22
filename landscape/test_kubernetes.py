from .kubernetes import provisioner_from_context_name

def test_provisioner_from_context_name_minikube():
	assert provisioner_from_context_name('minikube') == 'minikube'

def test_provisioner_from_context_name_gke():
	assert provisioner_from_context_name('gke_dummy') == 'terraform'
