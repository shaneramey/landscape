#! /usr/bin/env bash
#
# Purge a namespace (specified object types)
# Usage:
# purge.sh namespace_name
# Runs:
#  - helm delete --purge --namespace
#  - kubectl delete  --namespace

K8S_NAMESPACE=$1

# list should mirror https://github.com/kubernetes/helm/blob/f7f85526448592a3785e00d5da0f51f03fc2a7a2/pkg/tiller/kind_sorter.go#L57
k8s_purge_object_types=(
	ingress
	service
	cronjob
	job
	statefulset
	deployment
	replicaset
	replicationcontroller
	pod
	daemonset
	rolebinding
#	clusterrolebinding # FIXME: non-namespaced. Delete this after all namespaces
#	clusterrole # FIXME: non-namespaced. Delete this after all namespaces
	serviceaccount
	persistentvolumeclaim
#	persistentvolume # FIXME: non-namespaced. Delete this after all namespaces
	configmap
	secret
	limitrange
	resourcequota
)

TILLER_NAMESPACE=kube-system


function purge_namespace() {
	namespace_to_purge=$1

	echo "Deleting Helm kube-system ConfigMaps for all releases in namespace ${namespace_to_purge}:"
	helm_releases_in_namespace=`$helm_releases_in_namespace_command`
	echo $helm_releases_in_namespace | tr ' ' '\n'

	for release in $helm_releases_in_namespace; do
		helm_configmaps_for_release=`kubectl get configmap --namespace=$TILLER_NAMESPACE -o 'jsonpath={.items[*].metadata.name}' | tr ' ' '\n' | grep ${release}\.`
		for cfg in $helm_configmaps_for_release; do
			echo "  - $cfg"
			echo running kubectl delete --namespace=$TILLER_NAMESPACE configmap $cfg
			kubectl delete --namespace=$TILLER_NAMESPACE configmap $cfg
		done
	done

	echo "Deleting following object types in ${namespace_to_purge}:"
	for resource_type in ${k8s_purge_object_types[@]}; do
		echo " - $resource_type"
		echo running kubectl delete --namespace=$namespace_to_purge $resource_type --all
		kubectl delete --namespace=$namespace_to_purge $resource_type --all
	done

	echo Deleting namespace ${namespace_to_purge}
	kubectl delete namespace ${namespace_to_purge}
}

if [ "$K8S_NAMESPACE" == "__all_namespaces__" ]; then
	echo Purging everything in all namespaces
	namespace_list=`kubectl get ns -o jsonpath='{.items[*].metadata.name}' | grep -v kube-system`
	for ns in $namespace_list; do
		echo
		echo "Purging namespace $ns"
		echo
		purge_namespace $ns
	done
else
	echo Purging everything in namespace $K8S_NAMESPACE
	purge_namespace $K8S_NAMESPACE
fi
