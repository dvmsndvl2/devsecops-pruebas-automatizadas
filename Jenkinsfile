pipeline {
    agent any
    environment {
        SCANNER_HOME = tool 'SonarScanner'
    }
    stages {
        stage('Build') {
            steps {
                echo '=== [BUILD] Instalando dependencias del proyecto ==='
                sh 'pip install --no-cache-dir --ignore-installed -r requirements.txt --break-system-packages || true'
            }
        }
        stage('Test') {
            steps {
                echo '=== [TEST] Ejecutando pruebas unitarias con Pytest ==='
                sh 'pytest test_app.py -v'
            }
        }
        stage('Analyze') {
            steps {
                echo '=== [ANALYZE] Escaneo de código SAST con SonarQube ==='
                withSonarQubeEnv('SonarQube') {
                    sh "${SCANNER_HOME}/bin/sonar-scanner"
                }
            }
        }
        stage('Deploy') {
            steps {
                echo '=== [DEPLOY] Levantando aplicacion para pruebas DAST ==='
                sh '''
                    docker rm -f vulnerable-flask-app || true
                    docker build -t vulnerable-flask:latest .
                    docker run -d --name vulnerable-flask-app --net devsecops-net -p 5000:5000 vulnerable-flask:latest
                    sleep 5
                    curl -I http://vulnerable-flask-app:5000/hello?name=Test || true
                '''
            }
        }
        stage('Security Test') {
            steps {
                echo '=== [SECURITY TEST] 1. OWASP Dependency-Check (SCA) ==='
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    dependencyCheck additionalArguments: '--scan . --format HTML --format XML --project "Flask Vulnerable App"', odcInstallation: 'DP-Check'
                    dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
                }
                echo '=== [SECURITY TEST] 2. OWASP ZAP (DAST) ==='
                sh '''
                    # Dar permisos a la carpeta para que ZAP guarde el reporte HTML
                    chmod -R 777 ${WORKSPACE} || true
                    docker run --rm \
                      --net devsecops-net \
                      -v ${WORKSPACE}:/zap/wrk/:rw \
                      zaproxy/zap-stable \
                      zap-baseline.py \
                      -t http://vulnerable-flask-app:5000/hello?name=Test \
                      -r zap_report.html || true
                '''
            }
        }
    }
    post {
        always {
            sh 'docker rm -f vulnerable-flask-app || true'
        }
    }
}
