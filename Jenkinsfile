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
            steps {
                echo "Setting environment branch: ${env.BRANCH_NAME}"
                echo "clusterDomain: ${env.BRANCH_NAME}.local"
                echo "echo make PROVISIONER=${params.PROVISIONER} environment"
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
                echo 'make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} deploy'
                sh 'make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} deploy'
                sh 'sleep 999999'
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
