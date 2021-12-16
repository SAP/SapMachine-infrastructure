#!/bin/bash
set -ex

NEXUS_PATH=https://common.repositories.cloud.sap/artifactory/sapmachine-mvn/sapmachine-build/devkit-macos-xcode
DEVKIT_VERSION=13.1
DEVKIT_BASENAME=$1

if [ -d ${DEVKIT_BASENAME} ]; then
  echo ${DEVKIT_BASENAME} already exists
  exit 0
fi

mkdir ${DEVKIT_BASENAME}
pushd ${DEVKIT_BASENAME}
curl -s -u ${ART_USER}:${ART_PASSWORD} ${NEXUS_PATH}/${DEVKIT_VERSION}/${DEVKIT_BASENAME}.tar.tgz --output ${DEVKIT_BASENAME}.tgz
tar xzf ${DEVKIT_BASENAME}.tgz
rm ${DEVKIT_BASENAME}.tgz
popd
echo extracted devkit to ${DEVKIT_BASENAME}
