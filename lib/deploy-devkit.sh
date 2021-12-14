#!/bin/bash
set -ex

NEXUS_PATH=https://common.repositories.cloud.sap/artifactory/sapmachine-mvn/sapmachine-build/devkit-macos-xcode
DEVKIT_VERSION=13.1
DEVKIT_BASENAME=$1

DEVKIT_PATH_UNRESOLVED=`pwd`/../${DEVKIT_BASENAME}

if [ -d $DEVKIT_PATH_UNRESOLVED ]; then
  DEVKIT_PATH=$(cd $DEVKIT_PATH_UNRESOLVED ; pwd)
  echo $DEVKIT_PATH already exists
  exit 0
fi

mkdir $DEVKIT_PATH_UNRESOLVED
pushd $DEVKIT_PATH_UNRESOLVED
curl -s -u ${ART_USER}:${ART_PASSWORD} ${NEXUS_PATH}/${DEVKIT_VERSION}/${DEVKIT_BASENAME}.tar.tgz --output ${DEVKIT_BASENAME}.tgz
tar xzf ${DEVKIT_BASENAME}.tgz
rm ${DEVKIT_BASENAME}.tgz
echo extracted devkit to `pwd`
popd
