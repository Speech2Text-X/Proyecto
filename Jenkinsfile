pipeline {
  agent any
  options {
    timestamps()
    disableConcurrentBuilds()
  }
  triggers {
    githubPush()
  }
  environment {
    WORKDIR = '.'
    COMPOSE_FILE = "docker-compose.yml"
    IMAGE_NAME = 's2x-api'
    REGISTRY = ''
    IMAGE_TAG = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'local'}"
    DEPLOY_HOST = ''
    DEPLOY_USER = ''
    DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1437531993469358121/3W1dEIwKvhhkxDeZjvP5Xu2i-CnkWrEng2HJ53mLljXOaBpFlHk4M4SgyQgzrUIH9x5u'
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'pwd && ls -la'
      }
    }

    stage('Build') {
      steps {
        dir("${WORKDIR}") {
          sh '''
            set -e
            compose() { docker compose "$@" || docker-compose "$@"; }
            compose build
          '''
        }
      }
    }

    stage('Test') {
      steps {
        dir("${WORKDIR}") {
          sh '''
            set -e
            compose() { docker compose "$@" || docker-compose "$@"; }

            compose up -d postgres

            for i in $(seq 1 30); do
              if compose exec -T postgres pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-s2x}; then
                echo "Postgres OK"; break
              fi
              echo "Esperando Postgres..."; sleep 2
            done

            mkdir -p backend/reports

            compose run --rm \
              -e S2X_DISABLE_WHISPER=1 \
              -v "$PWD/backend/reports":/app/reports \
              api sh -lc "pytest -q --maxfail=1 --disable-warnings --junitxml=/app/reports/pytest.xml"
          '''
        }
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'Proyecto/backend/reports/pytest.xml'
          dir("${WORKDIR}") {
            sh '''
              compose() { docker compose "$@" || docker-compose "$@"; }
              compose down -v || true
            '''
          }
        }
      }
    }

    stage('Build & Push Image') {
      when { expression { return env.REGISTRY?.trim() } }
      steps {
        dir("${WORKDIR}/backend") {
          withCredentials([usernamePassword(credentialsId: 'docker-registry', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
            sh '''
              set -e
              REG_HOST="${REGISTRY%%/*}"
              echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin "$REG_HOST"
              docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
              docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
              docker tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest
              docker push ${REGISTRY}/${IMAGE_NAME}:latest
            '''
          }
        }
      }
    }

    stage('Deploy') {
      when { expression { return env.DEPLOY_HOST?.trim() && env.REGISTRY?.trim() } }
      steps {
        sshagent(credentials: ['deploy-ssh']) {
          sh '''
            set -e
            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_HOST} '
              set -e
              cd /opt/s2x/Proyecto || exit 1
              git pull --rebase || true
              export IMAGE=${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
              docker compose pull || true
              docker compose up -d --build
            '
          '''
        }
      }
    }
  }
  post {
    success {
      script {
        if (env.DISCORD_WEBHOOK?.trim()) {
          def msg = "Build ${env.JOB_NAME} #${env.BUILD_NUMBER} OK (${env.GIT_BRANCH ?: 'n/a'} @ ${env.GIT_COMMIT?.take(7) ?: 'n/a'})"
          sh """curl -s -H 'Content-Type: application/json' -X POST -d '{\"content\":\"${msg}\"}' '${env.DISCORD_WEBHOOK}' || true"""
        }        
      }
    }
    failure {
      script {
        if (env.DISCORD_WEBHOOK?.trim()) {
          def msg = "Build ${env.JOB_NAME} #${env.BUILD_NUMBER} FAILED (${env.GIT_BRANCH ?: 'n/a'} @ ${env.GIT_COMMIT?.take(7) ?: 'n/a'})"
          sh """curl -s -H 'Content-Type: application/json' -X POST -d '{\"content\":\"${msg}\"}' '${env.DISCORD_WEBHOOK}' || true"""
        }        
      }
    }
  }
}


