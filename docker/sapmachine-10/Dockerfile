
FROM ubuntu:16.04

MAINTAINER Sapmachine <sapmachine@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_VERSION sapmachine-10+0

RUN set -eux;\
    cd /tmp;\
    curl -Lso sapmachine_linux-x64-sapmachine-10.0-jre.tar.gz https://github.com/SAP/SapMachine/releases/download/sapmachine-10%2B0/sapmachine_linux-x64-sapmachine-10.0-jre.tar.gz;\
    curl -Ls https://github.com/SAP/SapMachine/releases/download/sapmachine-10%2B0/sapmachine_linux-x64-sapmachine-10.0-jre.sha256.txt | sha256sum -c -;\
    mkdir -p /opt/java/sapmachine;\
    cd /opt/java/sapmachine;\
    tar -xf /tmp/sapmachine_linux-x64-sapmachine-10.0-jre.tar.gz;\
    rm -f /tmp/sapmachine_linux-x64-sapmachine-10.0-jre.tar.gz;

ENV PATH=/opt/java/sapmachine/jdk/bin:$PATH

