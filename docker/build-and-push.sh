#!/bin/bash
set -ex

if [[ $1 == "jre" ]]; then
  JRE=true
else
  JRE=false
fi

if [[ $2 == "alpine" ]]; then
  ALPINE=true
  ALPINE_EXT="-alpine"
else
  ALPINE=false
  ALPINE_EXT=
fi

REPO_URL="http://$GIT_USER:$GIT_PASSWORD@github.com/SAP/SapMachine-infrastructure/"

if [ ! -d infra ]; then
  git clone -b master $REPO_URL infra
fi

cd "infra/docker"

read VERSION_MAJOR VERSION_MINOR SAPMACHINE_VERSION VERSION_EXTENSION <<< $(echo $GIT_TAG_NAME | sed -rn 's/sapmachine\-([0-9]+)\+([0-9]+)\-?([0-9]*)(\-alpine)?/ \1 \2 \3 \4 /p')

set +e
docker ps -a | grep sapmachine | awk '{print $1}' | xargs docker rm
docker images | grep sapmachine | awk '{print $3}' | xargs docker rmi -f
set -e

if $JRE ; then
  docker build -t "$DOCKER_USER/jdk${VERSION_MAJOR}:${VERSION_MAJOR}.${VERSION_MINOR}.${SAPMACHINE_VERSION}-jre${ALPINE_EXT}" \
  -t "$DOCKER_USER/jdk${VERSION_MAJOR}:latest-jre${ALPINE_EXT}"  "sapmachine-$VERSION_MAJOR-jre${ALPINE_EXT}/."
else
  docker build -t "$DOCKER_USER/jdk${VERSION_MAJOR}:${VERSION_MAJOR}.${VERSION_MINOR}.${SAPMACHINE_VERSION}${ALPINE_EXT}" \
  -t "$DOCKER_USER/jdk${VERSION_MAJOR}:latest${ALPINE_EXT}"  "sapmachine-$VERSION_MAJOR${ALPINE_EXT}/."
fi
docker login -u $DOCKER_USER -p $DOCKER_PASSWORD
docker push "$DOCKER_USER/jdk${VERSION_MAJOR}"
