#! groovy

pipeline {
    agent any

    stages {
        stage('Environment') {
            steps {
                echo 'envconsul ...'
            }
        }
        stage('Test') {
            steps {
                echo 'landscaper apply --dry-run ...'
            }
        }
        stage('Deploy') {
            steps {
                echo 'landscaper apply ...'
            }
        }
    }
}
