GIT_BRANCH := $(shell git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3)

.PHONY: bootstrap deploy

bootstrap:
	landscaper apply --dir kube-system/nfs-provisioner/ --namespace=kube-system

deploy:
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
					[ $$? -ne 0 ] && exit 1 ; \
				fi ; \
			done ; \
		fi ; \
	done


