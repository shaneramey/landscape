#! /usr/bin/env bash

# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm charts
# Expects `kubectl config get-contexts` to have the desired context selected
# variables
#  - GIT_BRANCH (auto-discovered)
#  - vault_token passed in as argument, used for envconsul auth
# assumes you've authed to vault
set -u

namespace_arg=$1
# each branch has its own set of deployments
GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

darwin=false; # MacOSX compatibility
case "`uname`" in
    Darwin*) export sed_cmd=`which gsed` ;;
    *) export sed_cmd=`which sed` ;;
esac

function join_by {
    local IFS="$1"; shift; echo "$*";
}

function tell_to_populate_secrets {
    MISSING_SECRET_LIST=("$@")
    echo MISSING_SECRET_LIST $MISSING_SECRET_LIST
}

function generate_envconsul_config {
    GIT_BRANCH=$1
    K8S_NAMESPACE=$2
    CHART_NAME=$3

    # Envconsul Vault setup
    if [ ! -x $sed_cmd ]; then
        echo "ERROR: sed command $sed_cmd not found " \
            " (MacOS users: run brew install gnu-sed)"
        exit 2
    fi
    if [ ! -f /usr/local/bin/envconsul ]; then
        echo "envconsul not installed. aborting"
        exit 2
    fi

    V_PREFIX="/secret/landscape/$GIT_BRANCH/$K8S_NAMESPACE/$CHART_NAME"
    echo "    - Using Vault prefix $V_PREFIX"
    echo "    - Writing envconsul-config.hcl (.gitignored)"


    $sed_cmd "s/__GIT_BRANCH__/$GIT_BRANCH/g" envconsul-config.hcl.tmpl \
        > envconsul-config.hcl
    $sed_cmd -i "s/__K8S_NAMESPACE__/$K8S_NAMESPACE/g" envconsul-config.hcl
    $sed_cmd -i "s/__HELM_CHART__/$CHART_NAME/g" envconsul-config.hcl
}

function vault_to_env {
    GIT_BRANCH=$1
    CHART_NAME=$2
    K8S_NAMESPACE=$3

    # Generate envconsul config
    generate_envconsul_config $GIT_BRANCH $K8S_NAMESPACE $CHART_NAME
    # Read secrets from Vault
    ENVCONSUL_COMMAND="envconsul -config=./envconsul-config.hcl -secret="$V_PREFIX" -once -retry=1s -pristine -upcase env"
    echo "Running ${ENVCONSUL_COMMAND}:"
    for envvar_kv in `$ENVCONSUL_COMMAND`; do
        envvar_k=`echo $envvar_kv | awk -F= '{ print $1}'`
        echo "  - setting secret $envvar_k"
        export $envvar_kv
    done
}

function apply_namespace {
    K8S_NAMESPACE=$1

    missing_secret_list=() # in case any secrets are missing
    chart_errors=()

    # Apply landscape
    LANDSCAPER_COMMAND="landscaper apply -v --namespace=$K8S_NAMESPACE namespaces/$K8S_NAMESPACE/*.yaml"
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
        echo "lpass show k8s-landscaper/$GIT_BRANCH --notes"
        echo
        echo First read existing secrets, and see if you want to replace them
        echo
        echo vault read $V_PREFIX
        echo vault delete $V_PREFIX
        echo vault write $V_PREFIX \\
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

if [ "$namespace_arg" == "__all_namespaces__" ]; then
	# Loop through namespace
    for NAMESPACE_W_DIR in namespaces/*; do
        if [ -d $NAMESPACE_W_DIR ]; then
            NAMESPACE=`echo $NAMESPACE_W_DIR | awk -F/ '{ print $2 }'`
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
            for CHART_YAML in namespaces/${NAMESPACE}/*.yaml; do
                CHART_NAME=`cat $CHART_YAML | grep '^name: ' | awk -F': ' '{ print $2 }'`
                echo "Chart $CHART_NAME: exporting Vault secrets to env vars"
                echo "GIT_BRANCH=${GIT_BRANCH}"
                echo "CHART_NAME=${CHART_NAME}"
                echo "NAMESPACE=${NAMESPACE}"
                vault_to_env $GIT_BRANCH $CHART_NAME $NAMESPACE
            done
            # run landscaper
            apply_namespace $NAMESPACE
        fi
    done
else
    if [ -d "namespaces/$namespace_arg" ]; then
        echo "###"
        echo "# Namespace: $namespace_arg"
        echo "###"
        echo
        echo "Checking status of namespace $namespace_arg"
        kubectl get ns $namespace_arg > /dev/null
        if [ $? -eq 0 ]; then
            echo "    - Namespace $namespace_arg already exists"
        else
            echo -n "    - Namespace $namespace_arg does not exist. Creating..."
            kubectl create ns $namespace_arg
            echo " done."
        fi
        echo
        for CHART_YAML in namespaces/${namespace_arg}/*.yaml; do
        	CHART_NAME=`cat $CHART_YAML | grep '^name: ' | awk -F': ' '{ print $2 }'`
            echo "Chart $CHART_NAME: exporting Vault secrets to env vars"
            vault_to_env $GIT_BRANCH $CHART_NAME $namespace_arg
        done
        # run landscaper
        apply_namespace $namespace_arg
    fi
fi
