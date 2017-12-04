
FROM ubuntu:16.04

MAINTAINER Axel Siebenborn <axel.siebenborn@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_VERSION jdk10+34

RUN set -eux;\
    cd /tmp;\
    curl -Lso sapmachine_linux-x64-jdk-jdk10+34..tar.gz https://github.com/SAP/SapMachine/releases/download/jdk-jdk10+34%2B/sapmachine_linux-x64-jdk-jdk10+34..tar.gz;\
    curl -Ls https://github.com/SAP/SapMachine/releases/download/jdk-jdk10+34%2B/sapmachine_linux-x64-jdk-jdk10+34..sha256.txt | sha256sum -c -;\
    mkdir -p /opt/java/sapmachine;\
    cd /opt/java/sapmachine;\
    tar -xf /tmp/sapmachine_linux-x64-jdk-jdk10+34..tar.gz;\
    rm -f /tmp/sapmachine_linux-x64-jdk-jdk10+34..tar.gz;

ENV PATH=/opt/java/sapmachine/jdk/bin:$PATH

