#! /usr/bin/env bash

# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm charts
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

function generate_envconsul_config() {
    GIT_BRANCH=$1
    CHART_NAME=$2
    K8S_NAMESPACE=$3

    # Envconsul Vault setup
    if [ ! -x $sed_cmd ]; then
    	echo "ERROR: sed command $sed_cmd not found (MacOS users: run brew install gnu-sed)"
    	exit 2
    fi
    if [ ! -f /usr/local/bin/envconsul ]; then
    	echo "envconsul not installed. aborting"
    	exit 2
    fi

    echo "    - Using Vault prefix /secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME"
    echo "    - Writing envconsul-config.hcl (.gitignored)"


    $sed_cmd "s/__GIT_BRANCH__/$GIT_BRANCH/g" envconsul-config.hcl.tmpl > envconsul-config.hcl
    $sed_cmd -i "s/__K8S_NAMESPACE__/$K8S_NAMESPACE/g" envconsul-config.hcl
    $sed_cmd -i "s/__HELM_CHART__/$CHART_NAME/g" envconsul-config.hcl
}

function vault_to_env() {
	GIT_BRANCH=$1
	CHART_NAME=$2
	K8S_NAMESPACE=$3

	# Generate envconsul config
	generate_envconsul_config $GIT_BRANCH $NAMESPACE $CHART_NAME
	# Read secrets from Vault
	ENVCONSUL_COMMAND="envconsul -config="./envconsul-config.hcl" -secret="/secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME" -once -retry=1s -pristine -upcase env"
	echo "Running ${ENVCONSUL_COMMAND}:"
	for envvar_kv in `$ENVCONSUL_COMMAND`; do
		envvar_k=`echo $envvar_kv | awk -F= '{ print $1}'`
		echo "  - setting secret $envvar_k"
		export $envvar_kv
	done
}

function apply_namespace() {
	K8S_NAMESPACE=$1

	missing_secret_list=() # in case any secrets are missing
	chart_errors=()

	# Apply landscape
	LANDSCAPER_COMMAND="landscaper apply -v --namespace=$K8S_NAMESPACE $K8S_NAMESPACE/*.yaml"
	echo
	echo "Running \`$LANDSCAPER_COMMAND\`"
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
		echo
		echo NOTE: If you have lastpass-cli installed, run:
		echo
		echo "lpass show k8s\\\\k8s-landscaper/$GIT_BRANCH --notes"
		echo
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
	helm status ${K8S_NAMESPACE}-${CHART_NAME}
}

if [ -z $1 ]; then
	# Loop through namespace
	for NAMESPACE in *; do
		if [ -d $NAMESPACE ]; then
			echo "###"
			echo "# Namespace: $NAMESPACE"
			echo "###"
			echo
			echo "Checking status of namespace $NAMESPACE"
			kubectl get ns $NAMESPACE > /dev/null
			if [ $? -eq 0 ]; then
				echo "    - Namespace $NAMESPACE already exists"
			else
				echo -n "    - Namespace $NAMESPACE does not exist. Creating..."
				kubectl create ns $NAMESPACE
				echo " done."
			fi
			echo
			for CHART_YAML in ${NAMESPACE}/*.yaml; do
				if [ "$NAMESPACE" == "ca-pki-init" ] || [ "$NAMESPACE" == "docs" ] || [ "$NAMESPACE" == "bin" ]; then continue; fi # skip tls init workspace
				CHART_NAME=`cat $CHART_YAML | grep '^name: ' | awk -F': ' '{ print $2 }'`
				echo "Chart $CHART_NAME: exporting Vault secrets to env vars"
				vault_to_env $GIT_BRANCH $CHART_NAME $NAMESPACE
			done
			# run landscaper
			if [ "$NAMESPACE" == "ca-pki-init" ] || [ "$NAMESPACE" == "docs" ] || [ "$NAMESPACE" == "bin" ]; then continue; fi # skip tls init workspace
			apply_namespace $NAMESPACE
		fi
	done
else
	NAMESPACE=$1
	if [ -d $NAMESPACE ]; then
		echo "###"
		echo "# Namespace: $NAMESPACE"
		echo "###"
		echo
		echo "Checking status of namespace $NAMESPACE"
		kubectl get ns $NAMESPACE > /dev/null
		if [ $? -eq 0 ]; then
			echo "    - Namespace $NAMESPACE already exists"
		else
			echo -n "    - Namespace $NAMESPACE does not exist. Creating..."
			kubectl create ns $NAMESPACE
			echo " done."
		fi
		echo
		for CHART_YAML in ${NAMESPACE}/*.yaml; do
			if [ "$NAMESPACE" == "ca-pki-init" ] || [ "$NAMESPACE" == "docs" ] || [ "$NAMESPACE" == "bin" ]; then continue; fi # skip tls init workspace
			CHART_NAME=`cat $CHART_YAML | grep '^name: ' | awk -F': ' '{ print $2 }'`
			echo "Chart $CHART_NAME: exporting Vault secrets to env vars"
			vault_to_env $GIT_BRANCH $CHART_NAME $NAMESPACE
		done
		# run landscaper
		if [ "$NAMESPACE" == "ca-pki-init" ] || [ "$NAMESPACE" == "docs" ] || [ "$NAMESPACE" == "bin" ]; then continue; fi # skip tls init workspace
		apply_namespace $NAMESPACE
	fi
fi
