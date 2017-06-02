#! /usr/bin/env groovy

def getBranches() {
}

// get list of provisioners
def getProvisioners() {
    return ['minikube', 'kops']
}

def getTargets(provisioner) {
    minikube_target = nil
    kops_target = clustername
}

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
        booleanParam(name: 'DEBUG_BUILD', defaultValue: true, description: '')
    }

    triggers {
        pollSCM('* * * * *')
    }

    stages {

        stage('Environment') {
            steps {
                echo "make environment ${params.PERSON}"
                sh 'make environment'
            }
        }
        stage('Test') {
            steps {
                echo 'make test'
                sh 'make test'
            }
        }
        stage('Deploy') {
            steps {
                echo 'make deploy'
                sh 'make deploy'
            }
        }
        stage('Verify') {
            steps {
                echo 'make verify'
                sh 'make verify'
            }
        }
    }
}
