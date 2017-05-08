#! /usr/bin/env bash

# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm Charts
# Expects `kubectl config get-contexts` to have the desired context selected
# variables
#  - GIT_BRANCH (auto-discovered)
#  - 
set -u

# each branch has its own set of deployments
GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

# read secrets from Hashicorp Vault
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
if [ "$VAULT_TOKEN" == "" ]; then
	echo "ERROR: could not look up vault token. Auth first"
	exit 4
fi

darwin=false; # MacOSX compatibility
case "`uname`" in
	Darwin*) export sed_cmd=`which gsed` ;;
	*) export sed_cmd=`which sed` ;;
esac

function join_by { local IFS="$1"; shift; echo "$*"; }

function tell_to_populate_secrets {
	MISSING_SECRET_LIST=("$@")
	echo MISSING_SECRET_LIST $MISSING_SECRET_LIST 

}

function vault_to_env() {
	CHART=$1
	K8S_NAMESPACE=$2

	echo "    - Using Vault prefix /secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME"
	echo "    - Writing envconsul-config.hcl (.gitignored)"

	# Envconsul Vault setup
	if [ ! -x $sed_cmd ]; then
		echo "ERROR: sed command $sed_cmd not found (MacOS users: run brew install gnu-sed)"
		exit 2
	fi
	if [ ! -f /usr/local/bin/envconsul ]; then
		echo "envconsul not installed. aborting"
		exit 2
	fi
	$sed_cmd "s/__GIT_BRANCH__/$GIT_BRANCH/g" envconsul-config.hcl.tmpl > envconsul-config.hcl
	$sed_cmd -i "s/__K8S_NAMESPACE__/$K8S_NAMESPACE/g" envconsul-config.hcl
	$sed_cmd -i "s/__HELM_CHART__/$CHART_NAME/g" envconsul-config.hcl

	# Read secrets from Vault
	ENVCONSUL_COMMAND="envconsul -config="./envconsul-config.hcl" -secret="/secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME" -once -retry=1s -pristine -upcase env"
	echo "    - Running '$ENVCONSUL_COMMAND'"
	export $($ENVCONSUL_COMMAND 2> /dev/null) > /dev/null
}

function deploy_namespace() {
	K8S_NAMESPACE=$1

	missing_secret_list=() # in case any secrets are missing
	chart_errors=()

	# Apply landscape
	LANDSCAPER_COMMAND="landscaper apply --dir $K8S_NAMESPACE/ --namespace=$K8S_NAMESPACE"
	echo "    - Running '$LANDSCAPER_COMMAND'"
	LANDSCAPER_OUTPUT=`$LANDSCAPER_COMMAND 2>&1`
	echo "$LANDSCAPER_OUTPUT"
	while read -r line ; do
		MISSING_SECRET=`echo $line | awk '{ print $NF }' | cut -d= -f2 | tr '-' '_'`
		missing_secret_list+=("$MISSING_SECRET=${MISSING_SECRET}_value")
	done < <(echo "$LANDSCAPER_OUTPUT" | grep 'Secret\ not\ found\ in\ environment')

	# Print error if one exists
	while read -r line; do
		chart_errors+=("$line")
	done < <(echo "$LANDSCAPER_OUTPUT" | grep -i error)

	if [[ ${#missing_secret_list[@]} -ge 1 ]]; then
		echo
		echo '### WARNING WARNING WARNING'
		echo "It looks like you haven't set the secrets to provision this deployment."
		echo "The below commands will remove any pre-existing secrets in Vault."
		echo "They are to be used as a guide for initial provisioning of a deployment."
		echo "Other tools will leave pre-existing secret keys in Vault without wiping them. Use those tools for merges."
		echo
		missing_secret_count=${#missing_secret_list[@]}
		echo Vault is missing $missing_secret_count secrets.
		echo First read existing secrets, and see if you want to replace them
		echo
		echo vault read /secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME
		echo vault delete /secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME
		echo vault write /secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME \\
		for unset_secret in "${missing_secret_list[@]:0:missing_secret_count-1}"; do
			echo " " $unset_secret "\\"
		done
		echo " " ${missing_secret_list[missing_secret_count-1]}
		echo
		echo '### WARNING WARNING WARNING'
		echo
		exit 3
	fi

	if [[ ${#chart_errors[@]} -ge 1 ]]; then
		for chart_error in "${chart_errors[@]}"; do
			echo $chart_error
		done
		exit 2
	fi
}

# Main purpose here
helm repo update
for NAMESPACE in *; do
	if [ -d $NAMESPACE ]; then
		echo "Creating namespace $NAMESPACE with ImagePullSecrets (docker registry logins)"
		kubectl get ns $NAMESPACE
		if [ $? -ne 0 ]; then
			kubectl create ns $NAMESPACE
		fi
		# kubectl get secret --namespace=$NAMESPACE docker-registry gcr-json-key > /dev/null
		# if [ $? -ne 0 ]; then
		# 	# Download service account JSON from GCR
  #       	kubectl create secret --namespace=$NAMESPACE docker-registry gcr-json-key --docker-server=https://us.gcr.io --docker-username=_json_key --docker-password="$(cat ~/Downloads/downup-3baac25cc60e.json)" --docker-email=shane.ramey@gmail.com
		# fi
  #       kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "gcr-json-key"}]}' > /dev/null
		echo "Deploying Charts in namespace $NAMESPACE"
		for CHART_YAML in $NAMESPACE/*.yaml; do
			CHART_NAME=`cat $CHART_YAML | grep '^name: ' | awk -F': ' '{ print $2 }'`
			echo "Reading secrets from Vault for $CHART_NAME in namespace $NAMESPACE"
			vault_to_env $CHART_NAME $NAMESPACE
		done
		deploy_namespace $NAMESPACE
	fi
done
