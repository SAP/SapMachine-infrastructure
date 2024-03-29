#!/bin/bash
set -e

UNAME=$(uname)
ARTIFACTORY_PATH=https://common.repositories.cloud.sap/artifactory/sapmachine-mvn
DEVKIT_GROUP=$1
DEVKIT_GROUP_SLASH=`echo $DEVKIT_GROUP | tr . /`
DEVKIT_ARTEFACT=$2
DEVKIT_VERSION=$3
DEVKIT_BASENAME=${DEVKIT_ARTEFACT}-${DEVKIT_VERSION}
PARENT_DIR=$(cd .. && pwd)
if [[ $UNAME == Darwin ]]; then
  DEVKIT_ARCHIVE=${DEVKIT_BASENAME}.xip
  DEVKIT_PATH=${PARENT_DIR}/${DEVKIT_BASENAME}
  DEVKIT_ARCHIVE_PATH=${PARENT_DIR}/${DEVKIT_ARCHIVE}
elif [[ $UNAME == CYGWIN* ]]; then
  DEVKIT_ARCHIVE=${DEVKIT_BASENAME}.tar.gz
  DEVKIT_PATH="/cygdrive/c/devkits/${DEVKIT_BASENAME}"
  DEVKIT_ARCHIVE_PATH="/cygdrive/c/devkits/${DEVKIT_ARCHIVE}"
else
  DEVKIT_ARCHIVE=${DEVKIT_BASENAME}.tar.gz
  DEVKIT_PATH="/opt/devkits/${DEVKIT_BASENAME}"
  DEVKIT_ARCHIVE_PATH="/opt/devkits/${DEVKIT_ARCHIVE}"
fi

# We try to avoid unnecessary work by preparing the build agents with the devkit.
# However, should the local devkit of the requested version be missing, we'll download and extract it here.

# Check if the devkit in the well known location exists.
if [[ $UNAME != Darwin ]]; then
  if [ -d ${DEVKIT_PATH} ]; then
    echo Devkit directory ${DEVKIT_PATH} exists, using it.
    echo "${DEVKIT_PATH}" > devkitlocation.txt
    exit 0
  fi
  DEVKIT_PATH=${PARENT_DIR}/${DEVKIT_BASENAME}
fi

# Check once more whether it exists in the workspace.
if [ -d ${DEVKIT_PATH} ]; then
  echo Devkit directory ${DEVKIT_PATH} exists, using it.
  echo "${DEVKIT_PATH}" > devkitlocation.txt
  exit 0
fi

# OK, the devkit directory is not there. Check for the archive and download if necessary.
if [[ $UNAME != Darwin ]]; then
  if [ ! -f ${DEVKIT_ARCHIVE_PATH} ]; then
    DEVKIT_ARCHIVE_PATH=${PARENT_DIR}/${DEVKIT_ARCHIVE}
  fi
fi

if [ ! -f ${DEVKIT_ARCHIVE_PATH} ]; then
  echo Devkit archive ${DEVKIT_ARCHIVE_PATH} does not exist, need to download it.

  if [[ $UNAME == CYGWIN* ]]; then
    CURL_TOOL=/usr/bin/curl
  else
    CURL_TOOL=curl
  fi
  (set -x && ${CURL_TOOL} --version)

  DOWNLOAD_URL=${ARTIFACTORY_PATH}/${DEVKIT_GROUP_SLASH}/${DEVKIT_ARTEFACT}/${DEVKIT_VERSION}/${DEVKIT_ARCHIVE}
  HTTPRC=`${CURL_TOOL} -L -s -I -u ${ARTIFACTORY_CREDS} ${DOWNLOAD_URL} | head -n 1 | cut -d$' ' -f2`
  if [[ $HTTPRC -ne 200 ]]; then
    echo Error: ${DOWNLOAD_URL} is not downloadable, request returned $HTTPRC.
    exit -1
  fi
  echo Downloading ${DOWNLOAD_URL} to ${DEVKIT_ARCHIVE_PATH}...
  ${CURL_TOOL} -L -s -o ${DEVKIT_ARCHIVE_PATH} -u ${ARTIFACTORY_CREDS} ${DOWNLOAD_URL}
fi

# Now extract the devkit.
echo Extracting ${DEVKIT_ARCHIVE_PATH} to ${DEVKIT_PATH}...
if [[ $UNAME == Darwin ]]; then
  pushd ${PARENT_DIR}

  xip -x ${DEVKIT_ARCHIVE}
  mv Xcode.app ${DEVKIT_PATH}

  popd
else
  mkdir ${DEVKIT_PATH}
  pushd ${DEVKIT_PATH}

  if [[ $UNAME == "Linux" ]]; then
    tar --no-same-permissions --no-same-owner --strip-components=1 -xzf ${DEVKIT_ARCHIVE_PATH}
  else
    tar xzf ${DEVKIT_ARCHIVE_PATH}
  fi

  popd
fi

echo Extracted devkit.
echo "${DEVKIT_PATH}" > devkitlocation.txt
