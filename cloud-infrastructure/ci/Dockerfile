FROM jenkins/jenkins:lts

USER root
RUN apt-get update && apt-get install -qq -y --no-install-recommends \
git \
python \
ca-certificates \
wget


USER jenkins
RUN git clone https://github.com/sap/SapMachine-infrastructure /tmp/SapMachine-infrastructure
RUN python /tmp/SapMachine-infrastructure/lib/jenkins_restore.py -s /tmp/SapMachine-infrastructure -t /var/jenkins_home --install-plugins
RUN rm -rf /tmp/SapMachine-infrastructure

COPY init-sapmachine.groovy /usr/share/jenkins/ref/init.groovy.d/init-sapmachine.groovy
COPY read-sapmachine-pw.sh /usr/share/jenkins/read-sapmachine-pw.sh
COPY read-slave-secret.sh /usr/share/jenkins/read-slave-secret.sh


USER root
RUN mkdir /var/slaves
RUN mkdir /var/log/jenkins

RUN mkdir -p /var/pkg/deb/amd64
RUN mkdir -p /var/pkg/deb/keys
RUN mkdir -p /var/pkg/apk/3.5/x86_64
RUN mkdir -p /var/pkg/apk/keys

COPY keys/debian/* /var/pkg/deb/keys/
COPY keys/alpine/* /var/pkg/apk/keys/
COPY credentials.yml /var/slaves/credentials.yml
COPY log.properties /var/jenkins_home/log.properties

RUN chown -R jenkins:jenkins /var/log/jenkins
RUN chown -R jenkins:jenkins /var/pkg
RUN chown -R jenkins:jenkins /var/slaves
RUN chown jenkins:jenkins /usr/share/jenkins/ref/init.groovy.d/*.groovy
RUN chown jenkins:jenkins /var/slaves/credentials.yml
RUN chown jenkins:jenkins /usr/share/jenkins/read-sapmachine-pw.sh
RUN chown jenkins:jenkins /usr/share/jenkins/read-slave-secret.sh
RUN chown jenkins:jenkins /var/jenkins_home/log.properties
RUN chmod +x /usr/share/jenkins/read-sapmachine-pw.sh
RUN chmod +x /usr/share/jenkins/read-slave-secret.sh


USER jenkins
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Djava.util.logging.config.file=/var/jenkins_home/log.properties"
ENV JAVA_ARGS="-Xms10g"
VOLUME /var/pkg
VOLUME /var/slaves
VOLUME /var/log/jenkins
WORKDIR /var/jenkins_home
