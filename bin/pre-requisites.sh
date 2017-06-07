#! /usr/bin/env bash

LASTPASS_CLI_VERSION=1.1.2
VAULT_VERSION=0.7.0
ENVCONSUL_VERSION=0.6.2
KUBECTL_VERSION=1.6.2
HELM_VERSION=2.3.1
LANDSCAPER_VERSION=1.0.4

update_package_lists() {
	local platform_name=$2
}

get_version_for_platform() {
	local package_name=$(echo "$1" | tr '[:lower:]' '[:upper:]')
	local platform_name=$(echo "$2" | tr '[:lower:]' '[:upper:]')

	PLATFORM_SPECIFIC_VERSION="${platform_name}_${package_name}_VERSION"
	GENERIC_VERSION="${package_name}_VERSION"

	if [ -z "${!PLATFORM_SPECIFIC_VERSION}" ]; then
		echo "${!GENERIC_VERSION}"
	else
		echo "${!PLATFORM_SPECIFIC_VERSION}"
	fi
}

install_lastpass() {
#brew update
#brew install lastpass-cli --with-pinentry
}
install_vault() {
	local version=$1
	curl -LO https://releases.hashicorp.com/vault/${version}/vault_${version}_linux_amd64.zip && \
	unzip -d /usr/local/bin/ vault_${version}_linux_amd64.zip && \
	rm vault_${version}_linux_amd64.zip
}

install_envconsul() {
	local version=$1
	curl -LO https://releases.hashicorp.com/envconsul/${version}/envconsul_${version}_linux_amd64.zip && \
	unzip -d /usr/local/bin/ envconsul_${version}_linux_amd64.zip && \
	rm envconsul_${version}_linux_amd64.zip
}

install_kubectl() {
	local version=$1
	curl -LO https://storage.googleapis.com/kubernetes-release/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl && \
	chmod +x kubectl && \
	mv kubectl /usr/local/bin/

}

install_helm() {
	local version=$1
	curl -LO https://storage.googleapis.com/kubernetes-helm/helm-v${HELM_VERSION}-linux-amd64.tar.gz && \
	tar zvxf helm-v${HELM_VERSION}-linux-amd64.tar.gz --strip-components=1 linux-amd64/helm && \
	chmod +x helm && \
	mv helm /usr/local/bin/
}

install_package() {
	local package=$1
	local os=$2
	version=$(get_version_for_platform "${package}" "${os}")
	echo $version
}

main() {
	local os_name="$(uname)"
	update_package_lists "${os_name}"
	for program in lastpass vault envconsul kubectl helm landscaper; do
		install_package "${program}" "${os_name}"
	done
}

main
