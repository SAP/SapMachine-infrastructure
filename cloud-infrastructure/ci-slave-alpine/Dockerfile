FROM alpine:3.5

RUN apk update; \
    apk add bash; \
    apk add file; \
    apk add grep; \
    apk add make; \
    apk add zip; \
    apk add tar; \
    apk add python; \
    apk add git; \
    apk add shadow; \
    apk add openssh; \
    apk add alpine-sdk; \
    apk add openjdk8; \
    apk add curl;

ARG uid=1000
ARG gid=1000
ARG VERSION=3.21
ARG AGENT_WORKDIR=/home/jenkins/agent

ENV HOME /home/jenkins

RUN mkdir -p /var/cache/distfiles \
  && chmod a+w /var/cache/distfiles

RUN groupadd -g ${gid} jenkins \
  && useradd -ms /bin/bash jenkins -u ${uid} -g ${gid} -G abuild

RUN echo "jenkins    ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN echo "PACKAGER=\"SapMachine <sapmachine@sap.com>\"" >> /etc/abuild.conf
RUN echo "MAINTAINER=\"$PACKAGER\"" >> /etc/abuild.conf

RUN curl --create-dirs -sSLo /usr/share/jenkins/slave.jar https://repo.jenkins-ci.org/public/org/jenkins-ci/main/remoting/${VERSION}/remoting-${VERSION}.jar \
  && chmod 755 /usr/share/jenkins \
  && chmod 644 /usr/share/jenkins/slave.jar

COPY start-slave.sh /home/jenkins/start-slave.sh
RUN chmod +x /home/jenkins/start-slave.sh \
  && chown jenkins:jenkins /home/jenkins/start-slave.sh

USER jenkins
RUN abuild-keygen -a -i -n
ENV AGENT_WORKDIR=${AGENT_WORKDIR}
RUN mkdir /home/jenkins/.jenkins \
  && mkdir -p ${AGENT_WORKDIR}

VOLUME /home/jenkins/.jenkins
VOLUME ${AGENT_WORKDIR}
WORKDIR /home/jenkins

ENTRYPOINT /home/jenkins/start-slave.sh
