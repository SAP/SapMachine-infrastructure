#!/bin/bash
set -e

UNAME=$(uname)
NEXUS_PATH=https://common.repositories.cloud.sap/artifactory/sapmachine-mvn
DEVKIT_GROUP=$1
DEVKIT_GROUP_SLASH=`echo $DEVKIT_GROUP | tr . /`
DEVKIT_ARTEFACT=$2
DEVKIT_VERSION=$3
DEVKIT_BASENAME=${DEVKIT_ARTEFACT}-${DEVKIT_VERSION}
DEVKIT_ARCHIVE=${DEVKIT_BASENAME}.tar.gz

# We try to avoid unnecessary work by preparing the build agents with the devkit.
# However, should the local devkit of the requested version be missing, we'll download and extract it here.

# Here we check if the extracted devkit is present.
# On our Mac runners we had issues that an already extracted devkit folder went stale, so we don't do this for mac atm.
if [[ $UNAME != Darwin ]]; then
  if [[ $UNAME == CYGWIN* ]]; then
    DEVKIT_PATH="/cygdrive/c/devkits/${DEVKIT_BASENAME}"
  else
    DEVKIT_PATH="/opt/devkits/${DEVKIT_BASENAME}"
  fi

  if [ -d ${DEVKIT_PATH} ]; then
    echo Devkit directory ${DEVKIT_PATH} exists, using it.
    echo "${DEVKIT_PATH}" > devkitlocation.txt
    exit 0
  fi
fi

# OK, the devkit directory is not there. Do we already have the archive?
DEVKIT_PATH=$(pwd)"/${DEVKIT_BASENAME}"

if [[ $UNAME == Darwin ]]; then
  DEVKIT_ARCHIVE_PATH=$(cd .. && pwd)"/${DEVKIT_ARCHIVE}"
elif [[ $UNAME == CYGWIN* ]]; then
  DEVKIT_ARCHIVE_PATH="/cygdrive/c/devkits/${DEVKIT_ARCHIVE}"
else
  DEVKIT_ARCHIVE_PATH="/opt/devkits/${DEVKIT_ARCHIVE}"
fi

if [ ! -f ${DEVKIT_ARCHIVE_PATH} ]; then
  echo Devkit archive ${DEVKIT_ARCHIVE_PATH} does not exist, need to download it.
  if [[ $UNAME != Darwin ]]; then
    DEVKIT_ARCHIVE_PATH=$(pwd)"/${DEVKIT_ARCHIVE}"
  fi

  DOWNLOAD_URL=${NEXUS_PATH}/${DEVKIT_GROUP_SLASH}/${DEVKIT_ARTEFACT}/${DEVKIT_VERSION}/${DEVKIT_ARCHIVE}
  HTTPRC=`curl -L -s -I -u ${ARTIFACTORY_CREDS} ${DOWNLOAD_URL} | head -n 1 | cut -d$' ' -f2`
  if [[ $HTTPRC -ne 200 ]]; then
    echo Error: ${DOWNLOAD_URL} is not downloadable, request returned $HTTPRC.
    exit -1
  fi
  echo Downloading ${DOWNLOAD_URL} to ${DEVKIT_ARCHIVE_PATH} ...
  curl -L -s -o ${DEVKIT_ARCHIVE_PATH} -u ${ARTIFACTORY_CREDS} ${DOWNLOAD_URL}
fi

echo Extracting ${DEVKIT_ARCHIVE_PATH} to ${DEVKIT_PATH}...
mkdir ${DEVKIT_PATH}
pushd ${DEVKIT_PATH}
tar xzf ${DEVKIT_ARCHIVE_PATH}
popd
echo Extracted devkit.

echo "${DEVKIT_PATH}" > devkitlocation.txt
