#!/bin/bash
set -ex

# aarch64 or x64
PUBLISH_PLATFORM=$1

read VERSION OS_NAME<<< $(python3 ${WORKSPACE}/SapMachine-infrastructure/lib/publish_osx_get_version_osname.py -t ${SAPMACHINE_VERSION})

JDK_TGZ_NAME="sapmachine-jdk-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.tar.gz"
JDK_DMG_NAME="sapmachine-jdk-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.dmg"
JRE_TGZ_NAME="sapmachine-jre-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.tar.gz"
JRE_DMG_NAME="sapmachine-jre-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin.dmg"
SYMBOLS_TGZ_NAME="sapmachine-jdk-${VERSION}_${OS_NAME}-${PUBLISH_PLATFORM}_bin-symbols.tar.gz"

JDK_TGZ_SUM="$(echo $JDK_TGZ_NAME | sed 's/tar\.gz/sha256\.txt/')"
JDK_DMG_SUM="$(echo $JDK_DMG_NAME | sed 's/dmg/dmg\.sha256\.txt/')"
JRE_TGZ_SUM="$(echo $JRE_TGZ_NAME | sed 's/tar\.gz/sha256\.txt/')"
JRE_DMG_SUM="$(echo $JRE_DMG_NAME | sed 's/dmg/dmg\.sha256\.txt/')"
SYMBOLS_TGZ_SUM="$(echo $SYMBOLS_TGZ_NAME | sed 's/tar\.gz/sha256\.txt/')"

shasum -a 256 $JDK_TGZ_NAME > $JDK_TGZ_SUM
shasum -a 256 $JRE_TGZ_NAME > $JRE_TGZ_SUM
shasum -a 256 $SYMBOLS_TGZ_NAME > $SYMBOLS_TGZ_SUM
shasum -a 256 $JDK_DMG_NAME > $JDK_DMG_SUM
shasum -a 256 $JRE_DMG_NAME > $JRE_DMG_SUM

#debug, delete before using productively
SAPMACHINE_VERSION="sapmachine-0.0.0"

python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JDK_TGZ_NAME}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JDK_TGZ_SUM}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JDK_DMG_NAME}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JDK_DMG_SUM}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JRE_TGZ_NAME}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JRE_TGZ_SUM}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JRE_DMG_NAME}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${JRE_DMG_SUM}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${SYMBOLS_TGZ_NAME}"
python3 SapMachine-infrastructure/lib/github_publish.py -t $SAPMACHINE_VERSION -a "${SYMBOLS_TGZ_SUM}"

#debug, delete before using productively
exit 0

if [ "$PUBLISH_CASKS" == true ]; then
    python3 SapMachine-infrastructure/lib/make_cask.py -t $SAPMACHINE_VERSION
fi
