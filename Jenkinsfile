pipeline {
    options {
        buildDiscarder(logRotator(numToKeepStr: '10')) // Retain history on the last 10 builds
        timestamps() // Append timestamps to each line
        timeout(time: 20, unit: 'MINUTES') // Set a timeout on the total execution time of the job
    }
    agent any
    environment {
        HELM_PATH = "/var/jenkins_home/workspace/tutor-helm-generic"
        DISCORD_URL = "${params.DISCORD_URL}"
        PROJECT_NAME_ENV = "${params.PROJECT_NAME}-${params.TARGET_ENV}"
        PROJECT_BRANCH = "${params.PROJECT_NAME}/${params.TARGET_ENV}"
        KUBECONFIG_CREDENTIAL =  "kubeconfig-${params.PROJECT_NAME_TMP}-${params.TARGET_ENV}"
        DOCKER_REGISTRY = "${params.DOCKER_REGISTRY}"
    }
    stages {
        

        stage('Replace Variables') {
            steps {
                script {
                    try {
                        // Config replace
                        sh "sed -i -e 's#APP_NAME_VAR#${params.APP_NAME}#' ./cd/config.yaml;"
                        sh "sed -i -e 's#EXTERNAL_PORT#${params.EXTERNAL_PORT}#' ./cd/config.yaml;"
                        sh "sed -i -e 's#APP_HOST_VAR#${params.APP_HOST}#' ./cd/config.yaml;"
                        sh "sed -i -e 's#INTERNAL_PORT_VAR#${params.INTERNAL_PORT}#' ./cd/config.yaml;"
                        sh "sed -i -e 's#API_URL_VAR#${params.API_URL}#' ./cd/config.yaml;"
                        
                        sh "sed -i -e 's#APP_HOST_VAR#${params.APP_HOST}#' ./cd/ingress.yaml;"
                        sh "sed -i -e 's#K8S_NAMESPACE_VAR#${PROJECT_NAME_ENV}#' ./cd/ingress.yaml;"
                        sh "sed -i -e 's#APP_NAME_SERVICE_VAR#${params.APP_NAME}#' ./cd/ingress.yaml;"
                        sh "sed -i -e 's#INTERNAL_PORT_VAR#${params.INTERNAL_PORT}#' ./cd/ingress.yaml;"
                        
                        
                        
                    } catch (Exception e) {
                        echo "Error occurred: ${e.getMessage()}"
                        echo "${e.getStackTrace()}"
                        error "Failed to replace secrets variables"
                    }
                }
            }
        }
       

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImageTag = "${PROJECT_BRANCH}/${params.APP_NAME}:${BUILD_NUMBER}"
                    sh "docker build -t ${dockerImageTag} ."
                }
            }
        }

        stage('Push Docker Image to Registry') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'harbor-user', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]){
                        sh "docker login -u $USERNAME -p $PASSWORD ${DOCKER_REGISTRY}"
                        sh "docker tag ${dockerImageTag} ${DOCKER_REGISTRY}/${dockerImageTag}"
                        sh "docker push ${DOCKER_REGISTRY}/${dockerImageTag}"
                    }
                }
            }
        }


       stage('Prepare Helm Chart') {
            steps {
                script {
                    echo "Replace static var in config.yaml"
                    IMAGE_PATH = "${DOCKER_REGISTRY}/${PROJECT_BRANCH}"
                    sh "sed -i -e 's#IMAGE_PATH#${IMAGE_PATH}#' ./cd/config.yaml;"
                    sh "sed -i -e 's#BUILD_NUMBER#${BUILD_NUMBER}#' ./cd/config.yaml;"
                    sh "sed -i -e 's#APP_ENV_NAMESPACE#${PROJECT_NAME_ENV}#' ./cd/config.yaml;"
                    echo "Done!"

                    echo "Execute python script to create values.yaml"
                    sh "python3 ${HELM_PATH}/build-helm.py ${WORKSPACE}"
                    sh "python3 ${HELM_PATH}/generate_ingress.py ${WORKSPACE}"
                    echo "Done!"
                }
            }
        }

        stage('Deploy Helm Chart to Kubernetes') {
            steps {
                script {
                     withKubeConfig(credentialsId: KUBECONFIG_CREDENTIAL) {
                            sh "helm upgrade ${params.APP_NAME}-${params.TARGET_ENV} ${HELM_PATH}/application-helm-0.1.4.tgz --values ./values.yaml --install --namespace ${PROJECT_NAME_ENV}"
                            sh "kubectl apply -f ${WORKSPACE}/cd/ingress.yaml"
                        }
                }
            }
        }

        stage('Success Notify on Discord'){
            steps {
                script {
                    discordSend description: "[${params.TARGET_ENV}] - CI/CD Concluido com sucesso!", footer: "Ambiente atualizado em ${params.TARGET_ENV}", link: env.BUILD_URL, result: currentBuild.currentResult, title: JOB_NAME, webhookURL: "${params.DISCORD_URL}"
                }
            }
        }
    }

    post {
        failure {
            script {
                discordSend description: "[${params.TARGET_ENV}] - CI/CD Falhou!", footer: "Erro durante a execução em ${params.TARGET_ENV}", link: env.BUILD_URL, result: currentBuild.currentResult, title: JOB_NAME, webhookURL: "${params.DISCORD_URL}"
            }
        }
    }
}