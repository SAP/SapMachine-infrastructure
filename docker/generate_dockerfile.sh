#!/bin/bash
set -ex

JRE=false
JTREG=false
ALPINE=false
ALPINE_EXT=

while getopts ":rta" opt; do
  case $opt in
      r)
          echo "Build JRE image."
          JRE=true
          ;;
      t)
          echo "Build JTREG image."
          JTREG=true
          ;;
      a)
          echo "Build Alpine Linux image"
          ALPINE=true
          ALPINE_EXT="-alpine"
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

read VERSION_MAJOR VERSION_MINOR SAPMACHINE_VERSION<<< $(echo $GIT_TAG_NAME | sed -rn 's/sapmachine\-([0-9]+)\+([0-9]+)\-?([0-9]*)/ \1 \2 \3 /p')

if [ $JTREG == true ]; then
  cd "infra/test-docker"
else
  cd "infra/docker"
fi

DEPENDENCIES="wget ca-certificates"
if [ $JTREG == true ]; then
  if $ALPINE; then
    DEPENDENCIES="$DEPENDENCIES zip git unzip coreutils python binutils shadow"
  else
    DEPENDENCIES="$DEPENDENCIES zip git unzip realpath python binutils shadow"
  fi
  if $ALPINE; then
    ADD_USER="RUN groupadd -g 1001 jenkins; useradd -ms /bin/bash jenkins -u 1001 -g 1001"
  else
    ADD_USER="RUN useradd -ms /bin/bash jenkins -u 1001"
  fi
fi

if $JRE ; then
    FILENAME="sapmachine-$VERSION_MAJOR-jre$ALPINE_EXT/Dockerfile"

    if $ALPINE; then
        PACKAGE=sapmachine-$VERSION_MAJOR-jre=$VERSION_MAJOR.$VERSION_MINOR.$SAPMACHINE_VERSION-r0
    else
        PACKAGE=sapmachine-$VERSION_MAJOR-jre=$VERSION_MAJOR+$VERSION_MINOR.$SAPMACHINE_VERSION
    fi
else
    FILENAME="sapmachine-$VERSION_MAJOR$ALPINE_EXT/Dockerfile"

    if $ALPINE; then
        PACKAGE=sapmachine-$VERSION_MAJOR-jdk=$VERSION_MAJOR.$VERSION_MINOR.$SAPMACHINE_VERSION-r0
    else
        PACKAGE=sapmachine-$VERSION_MAJOR-jdk=$VERSION_MAJOR+$VERSION_MINOR.$SAPMACHINE_VERSION
    fi
fi

rm $FILENAME || true

if $ALPINE; then
cat >> $FILENAME << EOI

FROM alpine:3.5

RUN apk update; \
    apk add $DEPENDENCIES;

WORKDIR /etc/apk/keys
RUN wget https://sapmachine-ubuntu.sapcloud.io/alpine/sapmachine%40sap.com-5a673212.rsa.pub

WORKDIR /

RUN echo "http://sapmachine-ubuntu.sapcloud.io/alpine" >> /etc/apk/repositories

RUN apk update; \
    apk add $PACKAGE;

$ADD_USER

EOI
else
cat >> $FILENAME << EOI

FROM ubuntu:16.04

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \\
    && apt-get install -y --no-install-recommends $DEPENDENCIES \\
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://sapmachine-ubuntu.sapcloud.io/debian/sapmachine-debian.key | apt-key add - \\
    && echo "deb http://sapmachine-ubuntu.sapcloud.io/debian/amd64/ ./" >> /etc/apt/sources.list \\
    && apt-get update \\
    && apt-get -y --no-install-recommends install $PACKAGE

$ADD_USER

EOI
fi

git remote remove origin
git remote add origin $REPO_URL
git config user.email "sapmachine@sap.com"
git config user.name "SapMachine"

set +e
git commit -a -m "Update Dockerfile for $GIT_TAG_NAME"

git push origin master
set -e
