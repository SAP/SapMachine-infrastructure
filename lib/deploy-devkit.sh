#!/bin/bash
set -ex

NEXUS_PATH=https://common.repositories.cloud.sap/artifactory/sapmachine-mvn
DEVKIT_GROUP=$1
DEVKIT_GROUP_SLASH=`echo $DEVKIT_GROUP | tr . /`
DEVKIT_ARTEFACT=$2
DEVKIT_VERSION=$3
DEVKIT_BASENAME=${DEVKIT_ARTEFACT}-${DEVKIT_VERSION}
DEVKIT_ARCHIVE=${DEVKIT_BASENAME}.tar.gz

if [ -d ${DEVKIT_BASENAME} ]; then
  echo ${DEVKIT_BASENAME} already exists
  exit 0
fi

rm ../${DEVKIT_ARCHIVE} | true
if [ ! -f ../${DEVKIT_ARCHIVE} ]; then
  echo ${DEVKIT_ARCHIVE} does not exist, downloading...
  HTTPRC=`curl -L -s -I -u ${ART_USER}:${ART_PASSWORD} ${NEXUS_PATH}/${DEVKIT_GROUP_SLASH}/${DEVKIT_ARTEFACT}/${DEVKIT_VERSION}/${DEVKIT_ARCHIVE} | head -n 1 | cut -d$' ' -f2`
  if [[ $HTTPRC -eq 200 ]]; then
    echo File seems to be downloadable, request returned $HTTPRC.
  else
    echo Error: File not downloadable, request returned $HTTPRC.
    return -1
  fi
  curl -L -s -o ../${DEVKIT_ARCHIVE} -u ${ART_USER}:${ART_PASSWORD} ${NEXUS_PATH}/${DEVKIT_GROUP}/${DEVKIT_ARTEFACT}/${DEVKIT_VERSION}/${DEVKIT_ARCHIVE}
fi
ls -la ..

echo extracting devkit ${DEVKIT_BASENAME}...
mkdir ${DEVKIT_BASENAME}
pushd ${DEVKIT_BASENAME}
tar xzf ../../${DEVKIT_ARCHIVE}
popd
echo extracted devkit.
