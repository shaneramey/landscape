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
    }
}
