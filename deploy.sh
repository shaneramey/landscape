#! /usr/bin/env bash

# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm Charts

set -u

if [ -z ${VAULT_ADDR+x} ]; then
	echo "Configuration error. Set VAULT_ADDR (and other VAULT_ variables, if needed)"
	exit 2;
fi
vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | tail -n 1 | awk -F ': ' '{ print \$2 }'`
export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

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
function deploy_chart() {
	PATH_TO_CHART=$1
	K8S_NAMESPACE=$2

	CHART_NAME=`echo -n $PATH_TO_CHART | awk -F/ '{ print $2 }'`
	echo " - Deploying Chart $CHART_NAME"
	missing_secret_list=() # in case any secrets are missing
	chart_errors=()
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

	# Apply landscape
	LANDSCAPER_COMMAND="landscaper apply --dir $K8S_NAMESPACE/$CHART_NAME/ --namespace=$K8S_NAMESPACE"
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
		echo vault delete /secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME
		echo vault write /secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME \\
		for unset_secret in "${missing_secret_list[@]}"; do
			echo " " $unset_secret "\\"
		done
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
		echo "Deploying Charts in namespace $NAMESPACE"
		for CHART_PATH in $NAMESPACE/*; do
			if [ -d $CHART_PATH ]; then
				deploy_chart $CHART_PATH $NAMESPACE
			fi
		done
	fi
done
