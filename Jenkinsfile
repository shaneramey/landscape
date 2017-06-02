#! /usr/bin/env groovy

def getProvisioners() {
    return "minikube kops"
}

provisioners = getProvisioners();

pipeline {

    agent {
        node {
            label 'k8s-default'
        }
    }

    environment {
        VAULT_ADDR = "https://http.vault:8200"
    }

    options {
        timeout(time: 1, unit: 'HOURS') 
    }

    parameters {
        booleanParam(name: 'DEBUG_BUILD', defaultValue: true, description: 'turn on debugging')
        choice(name: 'PROVISIONER', choices: provisioners, description: 'cluster provisioner')
    }

    triggers {
        pollSCM('* * * * *')
    }

    stages {

        stage('Environment') {
            steps {
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
