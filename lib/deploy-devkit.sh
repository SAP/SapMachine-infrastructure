#!/bin/bash
set -ex

NEXUS_PATH=https://common.repositories.cloud.sap/artifactory/sapmachine-mvn
DEVKIT_GROUP=$1
DEVKIT_ARTEFACT=$2
DEVKIT_VERSION=$3
DEVKIT_BASENAME=${DEVKIT_ARTEFACT}-${DEVKIT_VERSION}
DEVKIT_ARCHIVE=${DEVKIT_BASENAME}.tar.gz

if [ -d ${DEVKIT_BASENAME} ]; then
  echo ${DEVKIT_BASENAME} already exists
  exit 0
fi

rm ../${DEVKIT_ARCHIVE}
if [ ! -f ../${DEVKIT_ARCHIVE} ]; then
  echo ${DEVKIT_ARCHIVE} does not exist, downloading...
  curl -L -s -o -u ${ART_USER}:${ART_PASSWORD} ${NEXUS_PATH}/${DEVKIT_GROUP}/${DEVKIT_ARTEFACT}/${DEVKIT_VERSION}/${DEVKIT_ARCHIVE} --output ../${DEVKIT_ARCHIVE}
  CURL_RC=$?
  if [[ $CURL_RC -eq 0 ]]; then
    echo curl returned $CURL_RC.
  else
    echo error: curl returned $CURL_RC.
    return -1
  fi
fi
ls -la ..

echo extracting devkit ${DEVKIT_BASENAME}...
mkdir ${DEVKIT_BASENAME}
pushd ${DEVKIT_BASENAME}
tar xzf ../../${DEVKIT_ARCHIVE}
popd
echo extracted devkit.
