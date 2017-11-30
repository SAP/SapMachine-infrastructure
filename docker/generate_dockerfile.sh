#!/bin/bash

FILENAME="Dockerfile"

if [ -z "$VERSION_TAG" ]; then
  echo "Missing mandatory environment variable VERSION_TAG"
fi

read VERSION_MAJOR VERSION_MINOR <<< $(echo $VERSION_TAG | sed -r 's/jdk\-([0-9]+)\+([0-9]*)/\1 \2/')

BASE_URL="https://github.com/SAP/SapMachine/releases/download/jdk-${VERSION_MAJOR}%2B${VERSION_MINOR}/"
ARCHIVE_NAME="sapmachine_linux-x64-jdk-${VERSION_MAJOR}.${VERSION_MINOR}.tar.gz"
SUM_NAME="sapmachine_linux-x64-jdk-${VERSION_MAJOR}.${VERSION_MINOR}.sha256.txt"
cat >> $FILENAME << EOI

FROM ubuntu:16.04

MAINTAINER Axel Siebenborn <axel.siebenborn@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \\
    && apt-get install -y --no-install-recommends curl ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_VERSION ${VERSION_TAG}

RUN set -eux;\\
    cd /tmp;\\
    curl -Lso $ARCHIVE_NAME $BASE_URL$ARCHIVE_NAME;\\
    curl -Ls $BASE_URL$SUM_NAME | sha256sum -c -;\\
    mkdir -p /opt/java/sapmachine;\\
    cd /opt/java/sapmachine;\\
    tar -xf /tmp/$ARCHIVE_NAME;\\
    rm -f /tmp/$ARCHIVE_NAME;

ENV PATH=/opt/java/sapmachine/jdk/bin:\$PATH

EOI
