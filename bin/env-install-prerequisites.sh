#! /usr/bin/env bash

LASTPASS_VERSION=1.2.0
VAULT_VERSION=0.7.3
ENVCONSUL_VERSION=0.6.2
KUBECTL_VERSION=1.6.2
HELM_VERSION=2.4.2
LANDSCAPER_VERSION=1.0.7
TERRAFORM_VERSION=0.9.9

# update_package_lists() {
#     local platform_name=$2
# }

get_version_for_platform() {
    package_name=$(echo "$1" | tr '[:lower:]' '[:upper:]')
    platform_name=$(echo "$2" | tr '[:lower:]' '[:upper:]')

    PLATFORM_SPECIFIC_VERSION="${platform_name}_${package_name}_VERSION"
    GENERIC_VERSION="${package_name}_VERSION"

    if [ -z "${!PLATFORM_SPECIFIC_VERSION}" ]; then
        echo "${!GENERIC_VERSION}"
    else
        echo "${!PLATFORM_SPECIFIC_VERSION}"
    fi
}

install_lastpass() {
    if ! [ -f '/usr/local/bin/lpass' ]; then
        brew update
        brew install lastpass-cli --with-pinentry
    else
        echo "lpass already installed"
    fi
}

install_vault() {
    if ! [ -f '/usr/local/bin/vault' ]; then
        local version=$1
        local platform=$2
        local download_file=vault_${version}_${platform}_amd64.zip
        curl -LO https://releases.hashicorp.com/vault/${version}/${download_file} && \
        unzip -d /usr/local/bin/ ${download_file} && \
        rm ${download_file}
    else
        echo "vault already installed"
    fi
}

install_envconsul() {
    if ! [ -f '/usr/local/bin/envconsul' ]; then
        local version=$1
        local platform=$2
        local download_file=envconsul_${version}_${platform}_amd64.zip
        curl -LO https://releases.hashicorp.com/envconsul/${version}/${download_file} && \
        unzip -d /usr/local/bin/ ${download_file} && \
        rm ${download_file}
    else
        echo "envconsul already installed"
    fi
}

install_kubectl() {
    if ! [ -f '/usr/local/bin/kubectl' ]; then
        local version=$1
        local platform=$2
        curl -LO https://storage.googleapis.com/kubernetes-release/release/v${KUBECTL_VERSION}/bin/${platform}/amd64/kubectl && \
        chmod +x kubectl && \
        mv kubectl /usr/local/bin/
    else
        echo "kubectl already installed"
    fi

}

install_helm() {
    if ! [ -f '/usr/local/bin/helm' ]; then
        local version=$1
        local platform=$2
        local download_file=helm-v${HELM_VERSION}-${platform}-amd64.tar.gz
        curl -LO https://storage.googleapis.com/kubernetes-helm/${download_file} && \
        tar zvxf ${download_file} --strip-components=1 ${platform}-amd64/helm && \
        chmod +x helm && \
        mv helm /usr/local/bin/ && \
        rm ${download_file}
    else
        echo "helm already installed"
    fi
}

install_landscaper() {
    if ! [ -f '/usr/local/bin/landscaper' ]; then
        local version=$1
        local platform=$2
        local download_file=landscaper-${LANDSCAPER_VERSION}-darwin-amd64.tar.gz
        curl -LO https://github.com/Eneco/landscaper/releases/download/${LANDSCAPER_VERSION}/${download_file} && \
        tar zxvf ${download_file} landscaper && \
        mv landscaper /usr/local/bin/ && \
        rm ${download_file}
    else
        echo "landscaper already installed"
    fi

}

install_terraform() {
    if ! [ -f '/usr/local/bin/terraform' ]; then
        local version=$1
        local platform=$2
        local download_file=terraform_${TERRAFORM_VERSION}_darwin_amd64.zip
        curl -LO https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/${download_file} && \
        unzip -d /usr/local/bin/ ${download_file} && \
        rm ${download_file}
    else
        echo "terraform already installed"
    fi
}

install_package() {
    local package=$1
    local os=`echo $2 | tr '[:upper:]' '[:lower:]'`
    version=$(get_version_for_platform "${package}" "${os}")
    echo "- Installing package ${package} version ${version} on OS ${os}"
    install_${package} $version $os
}

main() {
    os_name="$(uname)"
    #update_package_lists "${os_name}"
    for program in lastpass vault envconsul kubectl helm landscaper terraform; do
        install_package "${program}" "${os_name}"
    done

    # install Helm plugins
    if ! [ -d ~/.helm/plugins/helm-local-bump ]; then
        helm plugin install https://github.com/shaneramey/helm-local-bump
        pip3 install -r  ~/.helm/plugins/helm-local-bump/requirements.txt
    fi

    if ! [ -d ~/.helm/plugins/helm-template ]; then
        helm plugin install https://github.com/technosophos/helm-template \
        --version=2.4.1+2
        helm template -h # verify installed properly
    fi

}

main
