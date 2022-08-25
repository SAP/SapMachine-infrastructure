#!/bin/bash
set -ex

UNAME=`uname`

PRE_RELEASE_OPT="-p"
if [ "$RELEASE" == true ]; then
  PRE_RELEASE_OPT=""

  if [[ $UNAME == Darwin ]]; then
    exit 0
  fi
fi

if [[ -z $SAPMACHINE_GIT_REPOSITORY ]]; then
  SAPMACHINE_GIT_REPOSITORY="http://github.com/SAP/SapMachine.git"
fi

if [[ -z "$SAPMACHINE_VERSION" ]]; then
    echo "SAPMACHINE_VERSION not set"
    exit 1
fi
python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION $PRE_RELEASE_OPT || true

ls -la

ARCHIVE_NAME_JDK="$(cat jdk_bundle_name.txt)"
ARCHIVE_NAME_JRE="$(cat jre_bundle_name.txt)"
ARCHIVE_NAME_SYMBOLS="$(cat symbols_bundle_name.txt)"

HAS_ZIP=$(ls sapmachine-jdk-*_bin.zip | wc -l)

if [ "$HAS_ZIP" -lt "1" ]; then
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"
else
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/zip/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/zip/sha256\.txt/')"
fi
ARCHIVE_SUM_SYMBOLS="$(echo $ARCHIVE_NAME_SYMBOLS | sed 's/tar\.gz/sha256\.txt/')"

shasum -a 256 $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK
shasum -a 256 $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE
shasum -a 256 $ARCHIVE_NAME_SYMBOLS > $ARCHIVE_SUM_SYMBOLS

python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_NAME_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_SUM_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_SUM_SYMBOLS}"

if [ $UNAME == Darwin ]; then
    DMG_NAME_JDK="$(cat jdk_dmg_name.txt)"
    DMG_NAME_JRE="$(cat jre_dmg_name.txt)"

    DMG_SUM_JDK="$(echo $DMG_NAME_JDK | sed 's/dmg/dmg\.sha256\.txt/')"
    DMG_SUM_JRE="$(echo $DMG_NAME_JRE | sed 's/dmg/dmg\.sha256\.txt/')"

    shasum -a 256 $DMG_NAME_JDK > $DMG_SUM_JDK
    shasum -a 256 $DMG_NAME_JRE > $DMG_SUM_JRE

    python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_NAME_JDK}"
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_NAME_JRE}"
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_SUM_JDK}"
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_SUM_JRE}"
fi
