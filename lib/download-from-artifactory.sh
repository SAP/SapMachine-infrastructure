#!/bin/bash
set -ex

download_artifact() {
  DOWNLOAD_URL=$1
  TARGET_PATH=$2

  (set -x && curl --version)
  HTTPRC=`curl -L -s -I -u ${ARTIFACTORY_CREDS} ${DOWNLOAD_URL} | head -n 1 | cut -d$' ' -f2`
  if [[ $HTTPRC -ne 200 ]]; then
    echo Error: ${DOWNLOAD_URL} is not downloadable, request returned $HTTPRC.
    exit -1
  fi
  echo Downloading ${DOWNLOAD_URL} to ${TARGET_PATH}...
  curl -L -s -o ${TARGET_PATH} -u ${ARTIFACTORY_CREDS} ${DOWNLOAD_URL}
}

PLATFORM_ARG=$1
SMVERS=${SAPMACHINE_VERSION#sapmachine-}

JDK_TGZ_NAME=sapmachine-jdk_darwin${PLATFORM_ARG}64-${SMVERS}${NOTARIZED_SUFFIX}.tar.gz
JDK_TGZ_URL=${BINARY_SOURCE}/sapmachine-jdk_darwin${PLATFORM_ARG}64/${SMVERS}/${JDK_TGZ_NAME}

JDK_DMG_NAME=sapmachine-jdk_darwin${PLATFORM_ARG}64-${SMVERS}${NOTARIZED_SUFFIX}.dmg
JDK_DMG_URL=${BINARY_SOURCE}/sapmachine-jdk_darwin${PLATFORM_ARG}64/${SMVERS}/${JDK_DMG_NAME}

JRE_TGZ_NAME=sapmachine-jre_darwin${PLATFORM_ARG}64-${SMVERS}${NOTARIZED_SUFFIX}.tar.gz
JRE_TGZ_URL=${BINARY_SOURCE}/sapmachine-jre_darwin${PLATFORM_ARG}64/${SMVERS}/${JRE_TGZ_NAME}

JRE_DMG_NAME=sapmachine-jre_darwin${PLATFORM_ARG}64-${SMVERS}${NOTARIZED_SUFFIX}.dmg
JRE_DMG_URL=${BINARY_SOURCE}/sapmachine-jre_darwin${PLATFORM_ARG}64/${SMVERS}/${JRE_DMG_NAME}

SYMBOLS_NAME=sapmachine-symbols_darwin${PLATFORM_ARG}64-${SMVERS}.tar.gz
SYMBOLS_URL=${SYMBOL_SOURCE}/sapmachine-symbols_darwin${PLATFORM_ARG}64/${SMVERS}/${SYMBOLS_NAME}

download_artifact ${JDK_TGZ_URL} ${JDK_TGZ_NAME}
download_artifact ${JDK_DMG_URL} ${JDK_DMG_NAME}
download_artifact ${JRE_TGZ_URL} ${JRE_TGZ_NAME}
download_artifact ${JRE_DMG_URL} ${JRE_DMG_NAME}
download_artifact ${SYMBOLS_URL} ${SYMBOLS_NAME}
