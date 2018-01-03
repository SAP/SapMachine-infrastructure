#!/bin/bash
set -ex

if [[ $1 == "jre" ]]; then
  JRE=true
else
  JRE=false
fi

REPO_URL="http://$GIT_USER:$GIT_PASSWORD@github.com/SAP/SapMachine-infrastructure/"

if [ ! -d infra ]; then
  git clone -b master $REPO_URL infra
fi

cd "infra/docker"

read VERSION_MAJOR VERSION_MINOR <<< $(echo $VERSION_TAG | sed -r 's/sapmachine\-([0-9]+)\+([0-9]*)/\1 \2/')

if $JRE ; then
  docker build -t "$DOCKER_USER/jdk${VERSION_MAJOR}:${VERSION_MAJOR}.${VERSION_MINOR}-jre" \
  -t "$DOCKER_USER/jdk${VERSION_MAJOR}:latest-jre"  "sapmachine-$VERSION_MAJOR/."
else
  docker build -t "$DOCKER_USER/jdk${VERSION_MAJOR}:${VERSION_MAJOR}.${VERSION_MINOR}" \
  -t "$DOCKER_USER/jdk${VERSION_MAJOR}:latest"  "sapmachine-$VERSION_MAJOR/."
fi
docker login -u $DOCKER_USER -p $DOCKER_PASSWORD
docker push "$DOCKER_USER/jdk${VERSION_MAJOR}"
