#! /usr/bin/env bash
#
# Purge a namespace (specified object types)
# Usage:
# purge.sh namespace_name
# Runs:
#  - helm delete --purge --namespace
#  - kubectl delete  --namespace

K8S_NAMESPACE=$1
TILLER_NAMESPACE=kube-system

namespace_targets=()
helm_releases_in_namespace_command="helm list -q"
if [ "$K8S_NAMESPACE" != "__all_namespaces__" ]; then
	helm_releases_in_namespace_command="${helm_releases_in_namespace_command} --namespace=${K8S_NAMESPACE}"
fi
echo running $helm_releases_in_namespace_command
helm_releases_in_namespace=`$helm_releases_in_namespace_command`

echo "Deleting following Helm releases in namespace $K8S_NAMESPACE:"
echo $helm_releases_in_namespace | tr ' ' '\n'

for release in $helm_releases_in_namespace; do
	helm_configmaps_for_release=`kubectl get configmap --namespace=$TILLER_NAMESPACE -o 'jsonpath={.items[*].metadata.name}' | tr ' ' '\n' | grep ${release}\.`
	echo Deleting configmaps:
	for cfg in $helm_configmaps_for_release; do
		echo  - $cfg
		kubectl delete configmap --namespace=$TILLER_NAMESPACE $cfg
	done
done

echo "Deleting following object types in $K8S_NAMESPACE:"
k8s_delete_candidate_types=(deployment service configmap secret)

for resource_type in ${k8s_delete_candidate_types[@]}; do
	echo " - "$resource_type
	kubectl get --namespace=$K8S_NAMESPACE $resource_type -o 'jsonpath={.items[*].metadata.name}' | \
		xargs kubectl --namespace=$K8S_NAMESPACE delete $resource_type
done
	# deleting the configmaps above deregistered from helm, so this should error out
	# with 'no release found'
	#helm delete --purge $release
