#!/bin/bash
#set -ex
set -e

UNAME=`uname`
if [[ $UNAME == Darwin ]]; then
    SEDFLAGS='-E'
else
    SEDFLAGS='-r'
fi

if [[ -z $SAPMACHINE_VERSION ]]; then
  echo "SAPMACHINE_VERSION not set"
  exit 1
fi

if [[ -z $GITHUB_API_URL ]]; then
  GITHUB_API_URL_OPT=""
else
  GITHUB_API_URL_OPT=" -g $GITHUB_API_URL"
fi

if [[ -z $GITHUB_API_ORG ]]; then
  GITHUB_API_ORG_OPT=""
else
  GITHUB_API_ORG_OPT=" -o $GITHUB_API_ORG"
fi

if [ "$RELEASE" == true ]; then
  PRE_RELEASE_OPT=""
else
  PRE_RELEASE_OPT=" -p"
fi

python3 SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION}${PRE_RELEASE_OPT}${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}

ARCHIVE_NAME_JDK="$(cat jdk_bundle_name.txt)"
ARCHIVE_NAME_JRE="$(cat jre_bundle_name.txt)"
ARCHIVE_NAME_SYMBOLS="$(cat symbols_bundle_name.txt)"
ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed $SEDFLAGS 's/tar\.gz|zip/sha256\.txt/')"
ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed $SEDFLAGS 's/tar\.gz|zip/sha256\.txt/')"
ARCHIVE_SUM_SYMBOLS="$(echo $ARCHIVE_NAME_SYMBOLS | sed $SEDFLAGS 's/tar\.gz/sha256\.txt/')"

shasum -a 256 $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK
shasum -a 256 $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE
shasum -a 256 $ARCHIVE_NAME_SYMBOLS > $ARCHIVE_SUM_SYMBOLS

python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_NAME_JDK}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_NAME_JRE}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_NAME_SYMBOLS}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_SUM_JDK}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_SUM_JRE}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${ARCHIVE_SUM_SYMBOLS}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}

if [[ $UNAME == "Linux" ]] && [ "$RELEASE" == true ]; then
  for RPMFILE in *.rpm; do
    [ -f "$RPMFILE" ] || continue
    python3 SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${RPMFILE}${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
  done
fi

if [ $UNAME == Darwin ]; then
  DMG_NAME_JDK="$(cat jdk_dmg_name.txt)"
  DMG_NAME_JRE="$(cat jre_dmg_name.txt)"

  DMG_SUM_JDK="$(echo $DMG_NAME_JDK | sed $SEDFLAGS 's/dmg/dmg\.sha256\.txt/')"
  DMG_SUM_JRE="$(echo $DMG_NAME_JRE | sed $SEDFLAGS 's/dmg/dmg\.sha256\.txt/')"

  shasum -a 256 $DMG_NAME_JDK > $DMG_SUM_JDK
  shasum -a 256 $DMG_NAME_JRE > $DMG_SUM_JRE

  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_NAME_JDK}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_NAME_JRE}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_SUM_JDK}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
  python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${DMG_SUM_JRE}"${GITHUB_API_URL_OPT}${GITHUB_API_ORG_OPT}
fi

#if [[ $UNAME == CYGWIN* ]]; then
#  for MSIFILE in *.msi; do
#    shasum -a 256 $MSIFILE > ${MSIFILE}.sha256.txt
#    python3 SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${MSIFILE}
#    python3 SapMachine-infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${MSIFILE}.sha256.txt
#  done
#fi
