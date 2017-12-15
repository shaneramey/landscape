#! /usr/bin/env groovy
// pulls in HashiCorp vault env variables from environment
//  - VAULT_ADDR: address of Vault server
//  - VAULT_CACERT: CA cert that signed TLS cert on Vault server
//  if those are not set, fall back to in-cluster defaults

@Library('vaultHelpers') _

def convergeCharts(cluster_name, dry_run=true) {
    println("convergeCharts env ws="+env.WORKSPACE)
    def cmd = 'landscape charts converge --cluster=' + cluster_name
    if(dry_run) {
        cmd += " --dry-run"
    }
    println("Running command: " + cmd)
    sh cmd
}

def setupKubectlCredentials(cluster_name, dry_run=true) {
    def cmd = 'landscape cluster converge --cluster=' + cluster_name
    if(dry_run) {
        cmd += " --dry-run"
    }
    println("Running command: " + cmd)
    sh cmd
}

// properties([parameters([choice(choices: getClusterTargets().join('\n'), description: 'Kubernetes Context (defined in Vault)', name: 'CONTEXT', defaultValue: '')])])
properties([pipelineTriggers([cron('*/7 * * * *')])])


node('landscape') {
    stage('Checkout') {
        checkout scm
    }

    stage('Environment') {
        sh 'helm repo add chartmuseum http://http.chartmuseum.svc.cluster.local:8080'

        withEnv(['VAULT_ADDR='+vaultHelpers.getVaultAddr(),'VAULT_CACERT='+vaultHelpers.getVaultCacert(),'VAULT_TOKEN='+vaultHelpers.getVaultToken()]) {
            setupKubectlCredentials('gke_staging-165617_us-west1-a_master', false)
        }

    }

    stage('Test Charts ' + 'gke_staging-165617_us-west1-a_master') {
        withEnv(['VAULT_ADDR='+vaultHelpers.getVaultAddr(),'VAULT_CACERT='+vaultHelpers.getVaultCacert(),'VAULT_TOKEN='+vaultHelpers.getVaultToken()]) {
            convergeCharts('gke_staging-165617_us-west1-a_master', true)
        }
    }

    stage('Converge Charts ' + 'gke_staging-165617_us-west1-a_master') {
        withEnv(['VAULT_ADDR='+vaultHelpers.getVaultAddr(),'VAULT_CACERT='+vaultHelpers.getVaultCacert(),'VAULT_TOKEN='+vaultHelpers.getVaultToken()]) {
            convergeCharts('gke_staging-165617_us-west1-a_master', false)
        }
    }
}

