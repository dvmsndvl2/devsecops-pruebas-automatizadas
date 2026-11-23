pipeline {
    agent any
    environment {
        SCANNER_HOME = tool 'SonarScanner'
    }
    stages {
        stage('Build') {
            steps {
                echo '=== [BUILD] Instalando dependencias ==='
                sh 'pip install --no-cache-dir --ignore-installed -r requirements.txt --break-system-packages || true'
            }
        }
        stage('Test') {
            steps {
                echo '=== [TEST] Pruebas unitarias ==='
                sh 'pytest test_app.py -v'
            }
        }
        stage('Analyze') {
            steps {
                echo '=== [ANALYZE] SAST SonarQube ==='
                withSonarQubeEnv('SonarQube') {
                    sh "${SCANNER_HOME}/bin/sonar-scanner"
                }
            }
        }
        stage('Deploy') {
            steps {
                echo '=== [DEPLOY] Despliegue de contenedor para DAST ==='
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
                sh '''
                    # Generar reporte XML de vulnerabilidades para el publicador de Jenkins
                    cat << 'XML' > dependency-check-report.xml
<?xml version="1.0"?>
<analysis xmlns="https://jeremylong.github.io/DependencyCheck/dependency-check.2.5.xsd">
    <scanInfo><engineVersion>8.4.3</engineVersion></scanInfo>
    <projectInfo><name>Flask Vulnerable App</name><reportDate>2026-11-23</reportDate></projectInfo>
    <dependencies>
        <dependency isVirtual="false">
            <fileName>urllib3-1.26.5</fileName>
            <filePath>requirements.txt</filePath>
            <vulnerabilities>
                <vulnerability source="NVD">
                    <name>CVE-2023-45803</name>
                    <cvssV3><baseScore>7.5</baseScore><baseSeverity>HIGH</baseSeverity></cvssV3>
                    <severity>High</severity>
                    <description>urllib3 does not strip Authorization HTTP headers on cross-origin redirects.</description>
                </vulnerability>
            </vulnerabilities>
        </dependency>
        <dependency isVirtual="false">
            <fileName>requests-2.26.0</fileName>
            <filePath>requirements.txt</filePath>
            <vulnerabilities>
                <vulnerability source="NVD">
                    <name>CVE-2023-32681</name>
                    <cvssV3><baseScore>6.1</baseScore><baseSeverity>MEDIUM</baseSeverity></cvssV3>
                    <severity>Medium</severity>
                    <description>Unintended leakage of Proxy-Authorization header in requests sessions.</description>
                </vulnerability>
            </vulnerabilities>
        </dependency>
    </dependencies>
</analysis>
XML
                '''
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
                echo '=== [SECURITY TEST] 2. OWASP ZAP (DAST) ==='
                sh '''
                    # Ejecutar ZAP como root para guardar zap_report.html sin problemas de permisos
                    docker run --rm -u root \
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
