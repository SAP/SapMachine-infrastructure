#!/bin/bash
set -ex

JRE=false
JTREG=false

while getopts ":rt" opt; do
  case $opt in
      r)
          echo "Build JRE image."
          JRE=true
          ;;
      t)
          echo "Build JTREG image."
          JTREG=true
          ;;
      \?)
          echo "Invalid option: -$OPTARG" >&2
          ;;
  esac
done


if [ -z "$VERSION_TAG" ]; then
  echo "Missing mandatory environment variable VERSION_TAG"
fi

if [ -d infra ]; then
    rm -rf infra;
fi

REPO_URL="http://$GIT_USER:$GIT_PASSWORD@github.com/SAP/SapMachine-infrastructure/"
git clone -b master $REPO_URL infra

read VERSION_MAJOR VERSION_MINOR <<< $(echo $VERSION_TAG | sed -r 's/sapmachine\-([0-9]+)\+([0-9]*)/\1 \2/')

if [ $JTREG == true ]; then
  cd "infra/test-docker"
else
  cd "infra/docker"
fi

FILENAME="sapmachine-$VERSION_MAJOR/Dockerfile"

rm $FILENAME || true

DEPENDENCIES="wget ca-certificates"
if [ $JTREG == true ]; then
  DEPENDENCIES="$DEPENDENCIES zip git unzip realpath python"
fi

if $JRE ; then
    PACKAGE=sapmachine-$VERSION_MAJOR-jre=$VERSION_MAJOR+$VERSION_MINOR
else
    PACKAGE=sapmachine-$VERSION_MAJOR-jdk=$VERSION_MAJOR+$VERSION_MINOR
fi

cat >> $FILENAME << EOI

FROM ubuntu:16.04

MAINTAINER Sapmachine <sapmachine@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \\
    && apt-get install -y --no-install-recommends $DEPENDENCIES \\
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

git push origin master
set -e
