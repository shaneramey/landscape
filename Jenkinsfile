#! /usr/bin/env groovy

def clusterdomain = "${env.BRANCH_NAME}.local"

pipeline {
    agent any

    environment {
        VAULT_ADDR = "https://http.vault.svc.${clusterdomain}:8200"
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
                echo "clusterdomain: ${clusterdomain}"
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
