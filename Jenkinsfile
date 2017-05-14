#! groovy

pipeline {
    agent any

    stages {
        stage('Environment') {
            steps {
                echo 'make environment'
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
        stage('CSR Approve') {
            steps {
                echo 'make csr_approve'
                sh 'make csr_approve'
            }
        }
    }
}
