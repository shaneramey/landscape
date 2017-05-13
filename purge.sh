#! /usr/bin/env bash
#
# Purge a namespace (specified object types)
# Usage:
# purge.sh namespace_name
# Runs:
#  - helm delete --purge --namespace
#  - kubectl delete  --namespace

K8S_NAMESPACE=$1

k8s_purge_object_types=(deployment statefulset service configmap secrets)

TILLER_NAMESPACE=kube-system


function purge_namespace() {
	namespace_to_purge=$1

	echo "Deleting following Helm release ConfigMaps in namespace ${namespace_to_purge}:"
	helm_releases_in_namespace=`$helm_releases_in_namespace_command`
	echo $helm_releases_in_namespace | tr ' ' '\n'

	for release in $helm_releases_in_namespace; do
		helm_configmaps_for_release=`kubectl get configmap --namespace=$TILLER_NAMESPACE -o 'jsonpath={.items[*].metadata.name}' | tr ' ' '\n' | grep ${release}\.`
		for cfg in $helm_configmaps_for_release; do
			echo  - $cfg
			kubectl delete configmap --namespace=$TILLER_NAMESPACE $cfg
		done
	done

	echo "Deleting following object types in ${namespace_to_purge}:"
	for resource_type in ${k8s_purge_object_types[@]}; do
		echo " - "$resource_type
		kubectl --namespace=$namespace_to_purge delete $resource_type --all
	done

}

if [ "$K8S_NAMESPACE" == "__all_namespaces__" ]; then
	namespace_list=`kubectl get ns -o jsonpath='{.items[*].metadata.name}'`
	for ns in $namespace_list; do
		echo
		echo Purging namespace $ns
		echo
		purge_namespace $ns
	done
else
	purge_namespace $K8S_NAMESPACE
fi
