#! /usr/bin/env bash

# Deploys a Landscaper environment based on directory structure in this repo
# Each branch deploys its own set of Helm Charts

set -u

if [ -z ${VAULT_ADDR+x} ]; then
	echo "Configuration error. Set VAULT_ADDR (and other VAULT_ variables, if needed)"
	exit 2;
fi

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

darwin=false; # MacOSX compatibility
case "`uname`" in
  Darwin*) export sed_cmd=`which gsed` ;;
  *) export sed_cmd=`which sed` ;;
esac

function join_by { local IFS="$1"; shift; echo "$*"; }

for NAMESPACE in *; do
	if [ -d $NAMESPACE ]; then
		echo "Deploying Charts in namespace $NAMESPACE"
		for CHART_PATH in $NAMESPACE/*; do
			if [ -d $CHART_PATH ]; then
				CHART=`echo -n $CHART_PATH | awk -F/ '{ print $2 }'`
				echo " - Deploying Chart $CHART"
				missing_secret_list=() # in case any secrets are missing
				echo "    - Using Vault prefix /secret/landscape/$GIT_BRANCH/$NAMESPACE/$CHART"
				echo "    - Writing envconsul-config.hcl (.gitignored)"
				$sed_cmd "s/__GIT_BRANCH__/$GIT_BRANCH/g" envconsul-config.hcl.tmpl > envconsul-config.hcl
				$sed_cmd -i "s/__K8S_NAMESPACE__/$NAMESPACE/g" envconsul-config.hcl
				$sed_cmd -i "s/__HELM_CHART__/$CHART/g" envconsul-config.hcl

				ENVCONSUL_COMMAND="envconsul -config="./envconsul-config.hcl" -secret="/secret/landscape/$GIT_BRANCH/$NAMESPACE/$CHART" -once -retry=1s -pristine -upcase env"
				echo "    - Running '$ENVCONSUL_COMMAND'"
				export $($ENVCONSUL_COMMAND 2> /dev/null) > /dev/null

				LANDSCAPER_COMMAND="landscaper apply --dir $NAMESPACE/$CHART/ --namespace=$NAMESPACE"
				echo "    - Running '$LANDSCAPER_COMMAND'"
				while read -r line ; do
					MISSING_SECRET=`echo $line | awk '{ print $NF }' | cut -d= -f2 | tr '-' '_'`
					missing_secret_list+=("$MISSING_SECRET=${MISSING_SECRET}_value")
				done < <($LANDSCAPER_COMMAND 2>&1 | grep 'Secret\ not\ found\ in\ environment')

				if [[ ${#missing_secret_list[@]} -ge 1 ]]; then
					WRITE_STRING=$(join_by ' ' ${missing_secret_list[@]})
					echo
					echo '### WARNING WARNING WARNING'
					echo "It looks like you haven't set the secrets to provision this deployment."
					echo "The below commands will remove any pre-existing secrets in Vault."
					echo "They are to be used as a guide for initial provisioning of a deployment."
					echo "Other tools will leave pre-existing secret keys in Vault without wiping them. Use those tools for merges."
					echo
					echo vault delete /secret/landscape/$GIT_BRANCH/$NAMESPACE/$CHART
					echo vault write /secret/landscape/$GIT_BRANCH/$NAMESPACE/$CHART \\
					for unset_secret in "${missing_secret_list[@]}"; do
						echo " " $unset_secret "\\"
					done
					echo
					echo '### WARNING WARNING WARNING'
					echo
					exit 3
				fi
			fi
		done
	fi
done
