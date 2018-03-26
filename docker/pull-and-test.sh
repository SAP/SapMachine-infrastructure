#!/bin/bash

set -ex

if [[ $1 == "jre" ]]; then
    JRE=true
    JRE_EXT="-jre"
else
    JRE=false
    JRE_EXT=''
fi

VERSION_PRE_OPT="-ea"

if [ "$RELEASE" == true ]; then
  VERSION_PRE_OPT=""
fi

# delete local sapmachine images
set +e
docker ps -a | grep sapmachine | awk '{print $1}' | xargs docker rm
docker images | grep sapmachine | awk '{print $3}' | xargs docker rmi -f
set -e

read VERSION_MAJOR VERSION_MINOR SAPMACHINE_VERSION VERSION_EXTENSION<<< $(echo $GIT_TAG_NAME | sed -rn 's/sapmachine\-([0-9]+)\+([0-9]+)\-?([0-9]*)(\-alpine)?/ \1 \2 \3 \4 /p')
COMPARE_VERSION="OpenJDK Runtime Environment (build ${VERSION_MAJOR}${VERSION_PRE_OPT}+${VERSION_MINOR}-sapmachine-${SAPMACHINE_VERSION})"

TEST_VERSION=$(docker run "sapmachine/jdk${VERSION_MAJOR}:${VERSION_MAJOR}.${VERSION_MINOR}.${SAPMACHINE_VERSION}${JRE_EXT}" \
    java -version 2>&1 | grep 'OpenJDK Runtime Environment')

if [ "$TEST_VERSION" != "$COMPARE_VERSION" ]; then
    echo "Wrong version string"
    echo "Expected: $COMPARE_VERSION"
    echo "Got: $TEST_VERSION"
    exit 1
fi

JAVAC_PATH=$(docker run "sapmachine/jdk${VERSION_MAJOR}:${VERSION_MAJOR}.${VERSION_MINOR}.${SAPMACHINE_VERSION}${JRE_EXT}" \
    which javac) || true

if  $JRE && [ ! -z $JAVAC_PATH ]  ; then
    echo "javac found: $JAVAC_PATH"
    echo "seems not to be a JRE installation"
    exit 1
fi

if   [ ! $JRE ] && [ -z $JAVAC_PATH ]  ; then
    echo "No javac found"
    echo "seems not to be a JDK installation"
    exit 1
fi
