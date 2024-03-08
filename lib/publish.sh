#!/bin/bash
#set -ex
set -e

UNAME=`uname`

if [[ -z "$SAPMACHINE_VERSION" ]]; then
  echo "SAPMACHINE_VERSION not set"
  exit 1
fi

if [[ -z $SAPMACHINE_GIT_REPOSITORY ]]; then
  echo "SAPMACHINE_GIT_REPOSITORY not set"
  exit 1
fi

if [[ -z $GITHUB_API_URL ]]; then
  if [[ $SAPMACHINE_GIT_REPOSITORY == "*//github.com/*" ]]; then
    GITHUB_API_URL="https://api.github.com"
    echo "GitHub API URL set to $GITHUB_API_URL"
  else
    echo "GITHUB_API_URL not set or could not be determined from git repository URL ($SAPMACHINE_GIT_REPOSITORY)"
    exit 1
  fi
else
  echo "GitHub API URL is $GITHUB_API_URL"
fi

if [ "$RELEASE" == true ]; then
  PRE_RELEASE_OPT=""
else
  PRE_RELEASE_OPT="-p"
fi

python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL $PRE_RELEASE_OPT

ARCHIVE_NAME_JDK="$(cat jdk_bundle_name.txt)"
ARCHIVE_NAME_JRE="$(cat jre_bundle_name.txt)"
ARCHIVE_NAME_SYMBOLS="$(cat symbols_bundle_name.txt)"
ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/tar\.gz\|zip/sha256\.txt/')"
ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/tar\.gz\|zip/sha256\.txt/')"
ARCHIVE_SUM_SYMBOLS="$(echo $ARCHIVE_NAME_SYMBOLS | sed 's/tar\.gz/sha256\.txt/')"

shasum -a 256 $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK
shasum -a 256 $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE
shasum -a 256 $ARCHIVE_NAME_SYMBOLS > $ARCHIVE_SUM_SYMBOLS

python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${ARCHIVE_NAME_JDK}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${ARCHIVE_NAME_JRE}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${ARCHIVE_NAME_SYMBOLS}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${ARCHIVE_SUM_JDK}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${ARCHIVE_SUM_JRE}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${ARCHIVE_SUM_SYMBOLS}"

if [[ $UNAME == "Linux" ]] && [ "$RELEASE" == true ]; then
  for RPMFILE in *.rpm; do
    [ -f "$RPMFILE" ] || continue
    python3 SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -g $GITHUB_API_URL -a ${RPMFILE}
  done
fi

if [ $UNAME == Darwin ]; then
  DMG_NAME_JDK="$(cat jdk_dmg_name.txt)"
  DMG_NAME_JRE="$(cat jre_dmg_name.txt)"

  DMG_SUM_JDK="$(echo $DMG_NAME_JDK | sed 's/dmg/dmg\.sha256\.txt/')"
  DMG_SUM_JRE="$(echo $DMG_NAME_JRE | sed 's/dmg/dmg\.sha256\.txt/')"

  shasum -a 256 $DMG_NAME_JDK > $DMG_SUM_JDK
  shasum -a 256 $DMG_NAME_JRE > $DMG_SUM_JRE

  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${DMG_NAME_JDK}"
  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${DMG_NAME_JRE}"
  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${DMG_SUM_JDK}"
  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -g $GITHUB_API_URL -a "${DMG_SUM_JRE}"
fi

#if [[ $UNAME == CYGWIN* ]]; then
#  for MSIFILE in *.msi; do
#    shasum -a 256 $MSIFILE > ${MSIFILE}.sha256.txt
#    python3 SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${MSIFILE}
#    python3 SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${MSIFILE}.sha256.txt
#  done
#fi
