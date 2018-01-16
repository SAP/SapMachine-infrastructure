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


if [ -z "$GIT_TAG_NAME" ]; then
  echo "Missing mandatory environment variable VERSION_TAG"
fi

if [ -d infra ]; then
    rm -rf infra;
fi

REPO_URL="http://$GIT_USER:$GIT_PASSWORD@github.com/SAP/SapMachine-infrastructure/"
git clone -b master $REPO_URL infra

read VERSION_MAJOR VERSION_MINOR <<< $(echo $GIT_TAG_NAME | sed -r 's/sapmachine\-([0-9]+)\+([0-9]*)/\1 \2/')

if [ $JTREG == true ]; then
  cd "infra/test-docker"
else
  cd "infra/docker"
fi

DEPENDENCIES="wget ca-certificates"
if [ $JTREG == true ]; then
  DEPENDENCIES="$DEPENDENCIES zip git unzip realpath python binutils"
  ADD_USER="RUN useradd -ms /bin/bash jenkins -u 1001"
fi

if $JRE ; then
    FILENAME="sapmachine-$VERSION_MAJOR-jre/Dockerfile"
    PACKAGE=sapmachine-$VERSION_MAJOR-jre=$VERSION_MAJOR+$VERSION_MINOR
else
    FILENAME="sapmachine-$VERSION_MAJOR/Dockerfile"
    PACKAGE=sapmachine-$VERSION_MAJOR-jdk=$VERSION_MAJOR+$VERSION_MINOR
fi

rm $FILENAME || true

cat >> $FILENAME << EOI

FROM ubuntu:16.04

MAINTAINER Sapmachine <sapmachine@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \\
    && apt-get install -y --no-install-recommends $DEPENDENCIES \\
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://sapmachine-ubuntu.sapcloud.io/debian/sapmachine-debian.key | apt-key add - \\
    && echo "deb http://sapmachine-ubuntu.sapcloud.io/debian/amd64/ ./" >> /etc/apt/sources.list \\
    && apt-get update \\
    && apt-get -y --no-install-recommends install $PACKAGE

$ADD_USER

EOI

git remote remove origin
git remote add origin $REPO_URL
git config user.email "sapmachine@sap.com"
git config user.name "SapMachine"

set +e
git commit -a -m "Update Dockerfile for $GIT_TAG_NAME"

git push origin master
set -e
