.PHONY: bootstrap deploy

bootstrap:
	landscaper apply --dir kube-system/nfs-provisioner/ --namespace=kube-system

deploy:
	@for NAMESPACE in *; do \
	  if [[ -d $$NAMESPACE ]]; then \
		for CHART_PATH in $$NAMESPACE/*; do \
		  if [[ -d $$CHART_PATH ]]; then \
		    CHART=`echo -n $$CHART_PATH | awk -F/ '{ print $$2 }'` ; \
		    echo "Running 'landscaper apply --dir $$NAMESPACE/$$CHART/ --namespace=$$NAMESPACE'..." ; \
	        landscaper apply --dir $$NAMESPACE/$$CHART/ --namespace=$$NAMESPACE ; \
	        [ $$? -ne 0 ] && exit 1 ; \
	      fi ; \
	    done ; \
	  fi ; \
	done
