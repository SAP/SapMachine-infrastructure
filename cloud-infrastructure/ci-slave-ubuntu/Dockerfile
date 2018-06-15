FROM ubuntu:16.04

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
dh-make \
devscripts \
python \
git \
ca-certificates \
fakeroot \
make \
gcc \
g++ \
autoconf \
build-essential \
openjdk-8-jdk \
curl \
zip \
unzip \
wget \
realpath \
file

ARG uid=1000
ARG gid=1000
ARG VERSION=3.21
ARG AGENT_WORKDIR=/home/jenkins/agent

ENV HOME /home/jenkins

RUN groupadd -g ${gid} jenkins \
  && useradd -c "Jenkins user" -d $HOME -u ${uid} -g ${gid} -s /bin/bash -m jenkins

RUN curl --create-dirs -sSLo /usr/share/jenkins/slave.jar https://repo.jenkins-ci.org/public/org/jenkins-ci/main/remoting/${VERSION}/remoting-${VERSION}.jar \
  && chmod 755 /usr/share/jenkins \
  && chmod 644 /usr/share/jenkins/slave.jar

COPY start-slave.sh /home/jenkins/start-slave.sh
RUN chmod +x /home/jenkins/start-slave.sh \
  && chown jenkins:jenkins /home/jenkins/start-slave.sh

USER jenkins
ENV AGENT_WORKDIR=${AGENT_WORKDIR}
RUN mkdir /home/jenkins/.jenkins \
  && mkdir -p ${AGENT_WORKDIR} \
  && mkdir /home/jenkins/.gnupg

VOLUME /home/jenkins/.jenkins
VOLUME /home/jenkins/.gnupg
VOLUME ${AGENT_WORKDIR}
WORKDIR /home/jenkins

ENTRYPOINT /home/jenkins/start-slave.sh
