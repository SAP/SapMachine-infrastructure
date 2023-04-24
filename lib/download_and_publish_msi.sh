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

VERSION_NUMBER=${SAPMACHINE_VERSION#sapmachine-}

JDK_MSI_NAME=sapmachine-jdk-${VERSION_NUMBER}_windows-x64_bin.msi
JRE_MSI_NAME=sapmachine-jre-${VERSION_NUMBER}_windows-x64_bin.msi

download_artifact ${SOURCE_LOCATION}/${JDK_MSI_NAME} ${JDK_MSI_NAME}
download_artifact ${SOURCE_LOCATION}/${JRE_MSI_NAME} ${JRE_MSI_NAME}

shasum -a 256 ${JDK_MSI_NAME} > ${JDK_MSI_NAME}.sha256.txt
shasum -a 256 ${JRE_MSI_NAME} > ${JRE_MSI_NAME}.sha256.txt

python3 ${WORKSPACE}/SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${JDK_MSI_NAME}
python3 ${WORKSPACE}/SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${JDK_MSI_NAME}.sha256.txt

python3 ${WORKSPACE}/SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${JRE_MSI_NAME}
python3 ${WORKSPACE}/SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${JRE_MSI_NAME}.sha256.txt
