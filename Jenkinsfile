pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        PATH+HOMEBREW = '/opt/homebrew/bin'
        PATH+DOCKER = "${env.HOME}/.docker/bin"
        IMAGE_NAME = 'online-quiz-team73'
        CONTAINER_NAME = 'online-quiz-team73'
        DATA_VOLUME = 'online-quiz-team73-data'
        HOST_PORT = '8000'
        SECRET_CREDENTIAL_ID = 'flask-secret-key'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    def branchName = env.BRANCH_NAME?.trim()
                    if (!branchName) {
                        branchName = env.GIT_BRANCH?.trim()
                    }
                    if (!branchName || branchName == 'HEAD') {
                        branchName = sh(
                            script: 'git name-rev --name-only HEAD',
                            returnStdout: true
                        ).trim()
                    }
                    branchName = branchName.replaceFirst('^refs/heads/', '')
                    branchName = branchName.replaceFirst('^refs/remotes/', '')
                    branchName = branchName.replaceFirst('^remotes/origin/', '')
                    branchName = branchName.replaceFirst('^origin/', '')
                    branchName = branchName.replaceFirst('~.*$', '')
                    if (branchName == 'undefined') {
                        branchName = ''
                    }
                    if (branchName != 'main') {
                        error("Deployment pipeline only runs from main (checked out: '${branchName}').")
                    }
                }
            }
        }

        stage('Install dependencies') {
            steps {
                dir('Sprint2_S2-01_S2-14') {
                    sh '''
                        set -eu
                        python3.12 -m venv "$WORKSPACE_TMP/team73-python-env"
                        "$WORKSPACE_TMP/team73-python-env/bin/python" -m pip install \
                            -r requirements.txt \
                            -r requirements-dev.txt
                    '''
                }
            }
        }

        stage('Run automated tests') {
            steps {
                dir('Sprint2_S2-01_S2-14') {
                    sh '''
                        set -eu
                        DATABASE_PATH="$WORKSPACE_TMP/unused-test-import.db" \
                            "$WORKSPACE_TMP/team73-python-env/bin/python" -m pytest \
                            --cov=app --cov-branch \
                            --cov-report=term-missing \
                            --cov-report=html \
                            --cov-report=xml
                    '''
                }
            }
        }

        stage('Coverage report') {
            steps {
                archiveArtifacts artifacts: 'Sprint2_S2-01_S2-14/htmlcov/**,Sprint2_S2-01_S2-14/coverage.xml', fingerprint: true
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build --tag "$IMAGE_NAME:$BUILD_NUMBER" .'
            }
        }

        stage('Deploy container locally') {
            steps {
                withCredentials([string(credentialsId: env.SECRET_CREDENTIAL_ID, variable: 'SECRET_KEY')]) {
                    sh '''
                        set -eu
                        docker volume create "$DATA_VOLUME" >/dev/null
                        docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true
                        docker run --detach \
                            --name "$CONTAINER_NAME" \
                            --restart unless-stopped \
                            --publish "127.0.0.1:${HOST_PORT}:8000" \
                            --volume "$DATA_VOLUME:/data" \
                            --env APP_ENV=production \
                            --env DATABASE_PATH=/data/quiz.db \
                            --env SECRET_KEY \
                            "$IMAGE_NAME:$BUILD_NUMBER"
                    '''
                }
            }
        }

        stage('Verify application') {
            options {
                timeout(time: 2, unit: 'MINUTES')
            }
            steps {
                sh '''
                    set -eu
                    attempt=1
                    while [ "$attempt" -le 30 ]; do
                        if curl --fail --silent \
                            "http://127.0.0.1:${HOST_PORT}/login" >/dev/null; then
                            echo "Application is responding at http://127.0.0.1:${HOST_PORT}/login"
                            exit 0
                        fi
                        sleep 2
                        attempt=$((attempt + 1))
                    done
                    docker logs "$CONTAINER_NAME"
                    echo "Application did not become ready on localhost:${HOST_PORT}." >&2
                    exit 1
                '''
            }
        }
    }
}
