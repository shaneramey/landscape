#! /usr/bin/env groovy

pipeline {
    agent any

    environment {
        VAULT_ADDR = "https://http.vault.svc.${env.BRANCH_NAME}.local:8200"
        VAULT_CACERT = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    }

    options {
        timeout(time: 1, unit: 'HOURS') 
    }

    parameters {
        booleanParam(name: 'DEBUG_BUILD', defaultValue: true, description: 'turn on debugging')
        choice(name: 'PROVISIONER', choices: "minikube\nkops\ngke\n", description: 'cluster provisioner')
    }

    triggers {
        pollSCM('* * * * *')
    }

    stages {

        stage('Environment') {
            def vaultConfig = [$class: 'VaultConfiguration',
                                 vaultUrl: "${env.VAULT_ADDR}",
                                 vaultCredentialId: 'my-vault-cred-id']
            // inside this block your credentials will be available as env variables
            wrap([$class: 'VaultBuildWrapper', configuration: vaultConfig, vaultSecrets: secrets]) {
                sh 'vault list /secret'
            }

            steps {
                echo "Setting environment branch: ${env.BRANCH_NAME}"
                echo "clusterDomain: ${env.BRANCH_NAME}.local"
                echo "make PROVISIONER=${params.PROVISIONER} environment"
                sh 'make environment'
            }
        }
        stage('Test') {
            steps {
                echo 'make PROVISIONER=${params.PROVISIONER} test'
                sh 'make test'
            }
        }
        stage('Deploy') {
            steps {
                echo 'make PROVISIONER=${params.PROVISIONER} deploy'
                sh 'make deploy'
            }
        }
        stage('Verify') {
            steps {
                echo 'make PROVISIONER=${params.PROVISIONER} verify'
                sh 'make verify'
            }
        }
    }
}
