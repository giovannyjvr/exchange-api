pipeline {
  agent any
  environment {
    SERVICE = 'exchange'
    NAME = "giovannyjvr/${env.SERVICE}"
  }
  stages {
    stage('Dependencies') { steps { sh 'echo "no-op"' } }
    stage('Build & Push Image (multi-arch)') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credential', usernameVariable: 'USERNAME', passwordVariable: 'TOKEN')]) {
          sh '''
            docker login -u $USERNAME -p $TOKEN
            docker buildx create --use --platform=linux/arm64,linux/amd64               --node multi-platform-builder-${SERVICE}               --name multi-platform-builder-${SERVICE} || true
            docker buildx build --platform=linux/arm64,linux/amd64               --push -t ${NAME}:latest -t ${NAME}:${BUILD_ID} -f Dockerfile .
            docker buildx rm --force multi-platform-builder-${SERVICE} || true
          '''
        }
      }
    }
  }
}
