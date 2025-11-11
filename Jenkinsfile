pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds() }
  triggers { githubPush() }

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
            compose() { docker-compose "$@"; }
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
            compose() { docker-compose "$@"; }
            ci_compose() { docker-compose -f docker-compose.yml -f docker-compose.ci.yml "$@"; }

            # Limpieza previa
            docker rm -f s2x-postgres s2x-api >/dev/null 2>&1 || true
            compose down -v || true

            cat > docker-compose.ci.yml <<'YAML'
services:
  files:
    volumes:
      - s2x_files_data:/srv:ro

volumes:
  s2x_files_data:
    external: true
    name: s2x_files_data
YAML

            # Crear y precargar volumen externo
            docker volume rm -f s2x_files_data >/dev/null 2>&1 || true
            docker volume create s2x_files_data >/dev/null
            docker rm -f files_init >/dev/null 2>&1 || true
            docker create --name files_init -v s2x_files_data:/dest alpine:3.20 true
            ls -l frontend/public || true
            docker cp frontend/public/. files_init:/dest/
            docker rm -f files_init >/dev/null

            # Levantar DB + files
            ci_compose up -d postgres files

            # Esperar Postgres
            for i in $(seq 1 30); do
              if ci_compose exec postgres pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-s2x}; then
                echo "Postgres OK"; break
              fi
              echo "Esperando Postgres..."; sleep 2
            done

            # Aplicar SQL
            for f in db/00_*.sql db/01_schema.sql db/idx_*.sql; do
              [ -f "$f" ] || continue
              echo ">> Aplicando $f"
              ci_compose exec -T postgres bash -lc "psql -v ON_ERROR_STOP=1 -U \${POSTGRES_USER:-postgres} -d \${POSTGRES_DB:-s2x} -f /dev/stdin" < "$f"
            done

            ci_compose exec files sh -lc 'ls -l /srv && ls -l /srv/audio && test -f /srv/audio/audio.mp3'

            NET_NAME="$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' $(ci_compose ps -q files))"
            echo "Compose network: ${NET_NAME}"

            for i in $(seq 1 30); do
              if docker run --rm --network "${NET_NAME}" alpine:3.20 sh -lc 'wget -q --spider http://files/audio/audio.mp3'; then
                echo "files OK (http)"; break
              fi
              echo "Esperando files (http)..."; sleep 2
            done

            mkdir -p backend/reports

            # Ejecutar tests
            ci_compose run --rm \
              -v "$PWD/backend/reports":/app/reports \
              api sh -lc "pytest -q --disable-warnings --junitxml=/app/reports/pytest.xml"
          '''
        }
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'backend/reports/pytest.xml'
          dir("${WORKDIR}") {
            sh '''
              ci_compose() { docker-compose -f docker-compose.yml -f docker-compose.ci.yml "$@"; }
              ci_compose down -v || true
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
