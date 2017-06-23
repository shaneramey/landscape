#! /usr/bin/env groovy

def git_branch     = "${env.BRANCH_NAME}"
def cluster_domain = "${env.BRANCH_NAME}.local"

pipeline {
    agent any

    environment {
        VAULT_ADDR     = "https://http.vault.svc.${env.BRANCH_NAME}.local:8200"
        VAULT_CACERT   = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
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
                echo "using git branch: ${env.BRANCH_NAME}"
                echo "using clusterDomain: ${env.BRANCH_NAME}.local"
                sh "make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} environment"
            }
        }
        stage('Test') {
            steps {
                sh "echo make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} test"
                sh "make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} test"
            }
        }
        stage('Deploy') {
            steps {
                withCredentials([[$class: 'UsernamePasswordMultiBinding',
                                  credentialsId: 'vault',
                                  usernameVariable: 'VAULT_USER',
                                  passwordVariable: 'VAULT_PASSWORD']]) {
                    sh "vault auth -method=ldap username=$VAULT_USER password=$VAULT_PASSWORD && export VAULT_TOKEN=\$(vault read -field id auth/token/lookup-self) && make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} deploy && echo $VAULT_TOKEN"
                }
                sh 'sleep 999999'
            }
        }
        stage('Verify') {
            steps {
                sh "echo make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} verify"
                sh "make GIT_BRANCH=${env.BRANCH_NAME} PROVISIONER=${params.PROVISIONER} verify"
            }
        }
    }
}
