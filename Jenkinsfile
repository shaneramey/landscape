#! /usr/bin/env groovy
// pulls in HashiCorp vault env variables from environment
//  - VAULT_ADDR: address of Vault server
//  - VAULT_CACERT: CA cert that signed TLS cert on Vault server
//  if those are not set, fall back to in-cluster defaults


def getVaultAddr() {
    // in-cluster default vault server address; can be overridden below
    def vault_address = 'https://http.vault.svc.cluster.local:8200'
    def environment_configured_vault_addr = env.VAULT_ADDR
    if(environment_configured_vault_addr?.trim()) {
        vault_address = environment_configured_vault_addr
    }
    return vault_address
}

def getVaultCacert() {
    // in-cluster default vault ca certificate; can be overridden below
    def vault_cacertificate = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
    def environment_configured_vault_cacert = env.VAULT_CACERT
    if(environment_configured_vault_cacert?.trim()) {
        vault_cacertificate = environment_configured_vault_cacert
    }
    return vault_cacertificate
}

def getVaultToken() {
    withCredentials([[$class: 'UsernamePasswordMultiBinding',
                      credentialsId: 'vault',
                      usernameVariable: 'VAULT_USER',
                      passwordVariable: 'VAULT_PASSWORD']]) {
        def vault_addr = getVaultAddr()
        def vault_cacert = getVaultCacert()
        def token_auth_cmd = ['sh', '-c', "PATH=/usr/bin VAULT_ADDR=${vault_addr} VAULT_CACERT=${vault_cacert} /usr/local/bin/vault auth -method=ldap username=$VAULT_USER password=$VAULT_PASSWORD"]
        println("Attempting auth with command: " + token_auth_cmd)
        sout = token_auth_cmd.execute().text
        auth_token = sout.split("\n")[3].split(" ")[1].toString()
        return auth_token
    }
}

def convergeCloud(cloud_name, dry_run=true) {
    println("convergeCloud env ws="+env.WORKSPACE)
    if(cloud_name != "minikube") {
        def cmd = "landscape cloud converge --cloud=" + cloud_name

        if(dry_run) {
            cmd += " --dry-run"
        }
        println("Running command: " + cmd)
        sh cmd
    } else {
        println("Skipping minikube cloud setup inside of Jenkins")
    }
}

def convergeCluster(cluster_name, dry_run=true) {
    println("convergeCluster env ws="+env.WORKSPACE)
    def cmd = 'landscape cluster converge --cluster=' + cluster_name

    if(dry_run) {
        cmd += " --dry-run"
    }
    println("Running command: " + cmd)
    sh cmd
}

def convergeCharts(cluster_name, dry_run=true) {
    println("convergeCharts env ws="+env.WORKSPACE)
    def cmd = 'landscape charts converge --cluster=' + cluster_name
    if(dry_run) {
        cmd += " --dry-run"
    }
    println("Running command: " + cmd)
    sh cmd
}

// properties([parameters([choice(choices: getClusterTargets().join('\n'), description: 'Kubernetes Context (defined in Vault)', name: 'CONTEXT', defaultValue: '')])])
properties([pipelineTriggers([cron('H/5 * * * *')])])


node('landscape') {
    stage('Checkout') {
        checkout scm
    }

    stage('Environment') {
        sh 'helm repo add chartmuseum http://http.chartmuseum.svc.cluster.local:8080'
    }

    stage('Test Cloud ' + 'minikube') {
        println("Test Cloud env ws="+env.WORKSPACE)
        withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
            convergeCloud('minikube', true)
        }
    }
    stage('Test Cluster ' + 'minikube') {
        withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
            convergeCluster('minikube', true)
        }
    }
    stage('Test Charts ' + 'minikube') {
        withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
            convergeCharts('minikube', true)
        }
    }
    stage('Converge Cloud ' + 'minikube') {
        withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
            convergeCloud('minikube', false)
        }
    }
    stage('Converge Cluster ' + 'minikube') {
        withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
            convergeCluster('minikube', false)
        }
    }
    stage('Converge Charts ' + 'minikube') {
        withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
            convergeCharts('minikube', false)
        }
    }

}
