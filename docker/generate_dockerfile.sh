#!/bin/bash
set -ex

if [[ $1 == "jre" ]]; then
  JRE=true
else
  JRE=false
fi

if [ -z "$VERSION_TAG" ]; then
  echo "Missing mandatory environment variable VERSION_TAG"
fi

if [ -d infra ]; then
    rm -rf infra;
fi

REPO_URL="http://$GIT_USER:$GIT_PASSWORD@github.com/SAP/SapMachine-infrastructure/"
#TODO change branch to master
git clone -b use-package-in-docker $REPO_URL infra

read VERSION_MAJOR VERSION_MINOR <<< $(echo $VERSION_TAG | sed -r 's/sapmachine\-([0-9]+)\+([0-9]*)/\1 \2/')

cd "infra/docker"

FILENAME="sapmachine-$VERSION_MAJOR/Dockerfile"

rm $FILENAME || true

if $JRE ; then
    PACKAGE=sapmachine-$VERSION_MAJOR-jre=$VERSION_MAJOR+$VERSION_MINOR
else
    PACKAGE=sapmachine-$VERSION_MAJOR-jdk=$VERSION_MAJOR+$VERSION_MINOR
fi

cat >> $FILENAME << EOI

FROM ubuntu:16.04

MAINTAINER Sapmachine <sapmachine@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \\
    && apt-get install -y --no-install-recommends wget ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - http://sapmachine-ubuntu.sapcloud.io/sapmachine-debian.key | apt-key add - \\
    && echo "deb http://sapmachine-ubuntu.sapcloud.io/amd64/ ./" >> /etc/apt/sources.list \\
    && apt-get update \\
    && apt-get -y --no-install-recommends install $PACKAGE

EOI

git remote remove origin
git remote add origin $REPO_URL
git config user.email "sapmachine@sap.com"
git config user.name "SapMachine"

set +e
git commit -a -m "Update Dockerfile for $VERSION_TAG"
#TODO change branch to master
git push origin use-package-in-docker
set -e
