#! groovy

pipeline {
    agent any

    stages {
        stage('Environment') {
            steps {
                echo './environment.sh'
                sh './environment.sh'
            }
        }
        stage('Test') {
            steps {
                echo './test.sh'
                sh './test.sh'
            }
        }
        stage('Deploy') {
            steps {
                echo './deploy.sh'
                sh './deploy.sh'
            }
        }
    }
}
