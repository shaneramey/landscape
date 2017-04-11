GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

.PHONY: bootstrap deploy

bootstrap:
	landscaper apply --dir kube-system/nfs-provisioner/ --namespace=kube-system

deploy:
	@vault auth `docker logs dev-vault 2>&1 | grep 'Root\ Token' | awk -F ': ' '{ print $2 }'`
	@export VAULT_TOKEN=$(vault read -field id auth/token/lookup-self)
	@missing_secret_list=()
	@POPULATE_VAULT_STRING=''
	@for NAMESPACE in *; do \
		if [[ -d $$NAMESPACE ]]; then \
			for CHART_PATH in $$NAMESPACE/*; do \
				if [[ -d $$CHART_PATH ]]; then \
					CHART=`echo -n $$CHART_PATH | awk -F/ '{ print $$2 }'` ; \
					echo "Using Vault prefix /secret/landscape/$(GIT_BRANCH)/$$NAMESPACE/$$CHART" ; \
					echo "  - Writing envconsul-config.hcl (.gitignored)" ; \
					sed -e "s/__GIT_BRANCH__/$(GIT_BRANCH)/g" envconsul-config.hcl.tmpl > envconsul-config.hcl ; \
					sed -i '' -e "s/__K8S_NAMESPACE__/$$NAMESPACE/g" envconsul-config.hcl ; \
					sed -i '' -e "s/__HELM_CHART__/$$CHART/g" envconsul-config.hcl ; \
					ENVCONSUL_COMMAND="envconsul -config="./envconsul-config.hcl" -secret="/secret/landscape/$(GIT_BRANCH)/$$NAMESPACE/$$CHART" -once -retry=1s -pristine -upcase env" ; \
					echo "  - Running \'$$ENVCONSUL_COMMAND\'" ; \
					$$ENVCONSUL_COMMAND ; \
					[ $$? -ne 0 ] && exit 1 ; \
					LANDSCAPER_COMMAND="landscaper apply --dir $$NAMESPACE/$$CHART/ --namespace=$$NAMESPACE" ; \
					echo "  - Running \'$$LANDSCAPER_COMMAND\'" ; \
					$$LANDSCAPER_COMMAND | grep 'Secret not found in environment' | while read -r line ; do \
						missing_secret_list+=$$(echo $$line | sed -e 's/.*secret=\(.*\)/\1/') ; \
					done ; \
					for missing_secret in "$${missing_secret_list[@]}" ; do \
						echo "ERROR Vault missing Secret /secret/landscape/$(GIT_BRANCH)/$$NAMESPACE/$$CHART/$$missing_secret" ; \
						POPULATE_VAULT_STRING="$$POPULATE_VAULT_STRING $$missing_secret=$${missing_secret}-value" ; \
						if [ $${missing_secret_list[@]} -ne 0 ]; then \
							echo ; \
							echo '### WARNING WARNING WARNING' ; \
							echo "It looks like you haven't set the secrets to provision this deployment." ; \
							echo "The below commands will remove any pre-existing secrets in Vault" ; \
							echo "They are to be used as a guide for initial provisioning of a deployment" ; \
							echo "Other tools will leave pre-existing secret keys in Vault without wiping them. Use those tools for merges" ; \
							echo ; \
							echo vault delete /secret/landscape/$(GIT_BRANCH)/$$NAMESPACE/$$CHART ; \
							echo vault write /secret/landscape/$(GIT_BRANCH)/$$NAMESPACE/$$CHART $$POPULATE_VAULT_STRING ; \
							echo ; \
							echo '### WARNING WARNING WARNING' ; \
						fi ; \
					done ; \
				fi ; \
			done ; \
		fi ; \
	done

