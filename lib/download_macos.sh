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

# aarch64 or x64
PUBLISH_PLATFORM=$1

SOURCE_PLATFORM=$PUBLISH_PLATFORM
if [ "$SOURCE_PLATFORM" = "x64" ]; then
    SOURCE_PLATFORM=intel64
fi

read VERSION OS_NAME<<< $(python3 ${WORKSPACE}/SapMachine-infrastructure/lib/publish_osx_get_version_osname.py -t ${SAPMACHINE_VERSION})

BINARY_SOURCE_PREFIX=${BINARY_SOURCE_PATTERN//%v/$VERSION}
BINARY_SOURCE_PREFIX=${BINARY_SOURCE_PREFIX//%p/$SOURCE_PLATFORM}

JDK_TGZ_NAME=sapmachine-jdk-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.tar.gz
JDK_TGZ_URL=${BINARY_SOURCE_PREFIX//%b/jdk}
JDK_TGZ_URL=${JDK_TGZ_URL//%x/tar.gz}

JDK_DMG_NAME=sapmachine-jdk-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.dmg
JDK_DMG_URL=${BINARY_SOURCE_PREFIX//%b/jdk}
JDK_DMG_URL=${JDK_DMG_URL//%x/dmg}

JRE_TGZ_NAME=sapmachine-jre-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.tar.gz
JRE_TGZ_URL=${BINARY_SOURCE_PREFIX//%b/jre}
JRE_TGZ_URL=${JDK_TGZ_URL//%x/tar.gz}

JRE_DMG_NAME=sapmachine-jre-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.dmg
JRE_DMG_URL=${BINARY_SOURCE_PREFIX//%b/jre}
JRE_DMG_URL=${JRE_DMG_URL//%x/dmg}

SYMBOLS_TGZ_NAME=sapmachine-jdk-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin-symbols.tar.gz
SYMBOLS_URL=${SYMBOL_SOURCE}/sapmachine-symbols_darwin${SOURCE_PLATFORM}/${VERSION}/sapmachine-symbols_darwin${SOURCE_PLATFORM}-${VERSION}.tar.gz

download_artifact ${JDK_TGZ_URL} ${JDK_TGZ_NAME}
download_artifact ${JDK_DMG_URL} ${JDK_DMG_NAME}
download_artifact ${JRE_TGZ_URL} ${JRE_TGZ_NAME}
download_artifact ${JRE_DMG_URL} ${JRE_DMG_NAME}
download_artifact ${SYMBOLS_URL} ${SYMBOLS_TGZ_NAME}
