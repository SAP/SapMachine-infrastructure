#!/bin/bash
set -ex

VERSION=$(python3 ${WORKSPACE}/SapMachine-Infrastructure/lib/get_tag_version_component.py -t $GIT_TAG_NAME)
MAJOR="${GIT_TAG_NAME:11:2}"

if [[ $MAJOR < 17 ]]; then
  OS_NAME=osx
else
  OS_NAME=macos
fi 

INTEL_ARCHIVE_NAME_JDK="sapmachine-jdk-${VERSION}_${OS_NAME}-x64_bin.tar.gz"
INTEL_ARCHIVE_NAME_JRE="sapmachine-jre-${VERSION}_${OS_NAME}-x64_bin.tar.gz"
INTEL_ARCHIVE_NAME_SYMBOLS="sapmachine-jdk-${VERSION}_${OS_NAME}-x64_bin-symbols.tar.gz"
INTEL_DMG_NAME_JDK="sapmachine-jdk-${VERSION}_${OS_NAME}-x64_bin.dmg"
INTEL_DMG_NAME_JRE="sapmachine-jre-${VERSION}_${OS_NAME}-x64_bin.dmg"
AARCH_ARCHIVE_NAME_JDK="sapmachine-jdk-${VERSION}_${OS_NAME}-aarch64_bin.tar.gz"
AARCH_ARCHIVE_NAME_JRE="sapmachine-jre-${VERSION}_${OS_NAME}-aarch64_bin.tar.gz"
AARCH_ARCHIVE_NAME_SYMBOLS="sapmachine-jdk-${VERSION}_${OS_NAME}-aarch64_bin-symbols.tar.gz"
AARCH_DMG_NAME_JDK="sapmachine-jdk-${VERSION}_${OS_NAME}-aarch64_bin.dmg"
AARCH_DMG_NAME_JRE="sapmachine-jre-${VERSION}_${OS_NAME}-aarch64_bin.dmg"

mv INTEL_JDK_TGZ $INTEL_ARCHIVE_NAME_JDK
mv INTEL_JRE_TGZ $INTEL_ARCHIVE_NAME_JRE
mv INTEL_SYMBOLS $INTEL_ARCHIVE_NAME_SYMBOLS
mv INTEL_JDK_DMG $INTEL_DMG_NAME_JDK
mv INTEL_JRE_DMG $INTEL_DMG_NAME_JRE
mv AARCH_JDK_TGZ $AARCH_ARCHIVE_NAME_JDK
mv AARCH_JRE_TGZ $AARCH_ARCHIVE_NAME_JRE
mv AARCH_SYMBOLS $AARCH_ARCHIVE_NAME_SYMBOLS
mv AARCH_JDK_DMG $AARCH_DMG_NAME_JDK
mv AARCH_JRE_DMG $AARCH_DMG_NAME_JRE

INTEL_ARCHIVE_SUM_JDK="$(echo $INTEL_ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
INTEL_ARCHIVE_SUM_JRE="$(echo $INTEL_ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"
INTEL_ARCHIVE_SUM_SYMBOLS="$(echo $INTEL_ARCHIVE_NAME_SYMBOLS | sed 's/tar\.gz/sha256\.txt/')"
INTEL_DMG_SUM_JDK="$(echo $INTEL_DMG_NAME_JDK | sed 's/dmg/sha256\.dmg\.txt/')"
INTEL_DMG_SUM_JRE="$(echo $INTEL_DMG_NAME_JRE | sed 's/dmg/sha256\.dmg\.txt/')"
AARCH_ARCHIVE_SUM_JDK="$(echo $AARCH_ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
AARCH_ARCHIVE_SUM_JRE="$(echo $AARCH_ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"
AARCH_ARCHIVE_SUM_SYMBOLS="$(echo $AARCH_ARCHIVE_NAME_SYMBOLS | sed 's/tar\.gz/sha256\.txt/')"
AARCH_DMG_SUM_JDK="$(echo $AARCH_DMG_NAME_JDK | sed 's/dmg/sha256\.dmg\.txt/')"
AARCH_DMG_SUM_JRE="$(echo $AARCH_DMG_NAME_JRE | sed 's/dmg/sha256\.dmg\.txt/')"

shasum -a 256 $INTEL_ARCHIVE_NAME_JDK > $INTEL_ARCHIVE_SUM_JDK
shasum -a 256 $INTEL_ARCHIVE_NAME_JRE > $INTEL_ARCHIVE_SUM_JRE
shasum -a 256 $INTEL_ARCHIVE_NAME_SYMBOLS > $INTEL_ARCHIVE_SUM_SYMBOLS
shasum -a 256 $INTEL_DMG_NAME_JDK > $INTEL_DMG_SUM_JDK
shasum -a 256 $INTEL_DMG_NAME_JRE > $INTEL_DMG_SUM_JRE
shasum -a 256 $AARCH_ARCHIVE_NAME_JDK > $AARCH_ARCHIVE_SUM_JDK
shasum -a 256 $AARCH_ARCHIVE_NAME_JRE > $AARCH_ARCHIVE_SUM_JRE
shasum -a 256 $AARCH_ARCHIVE_NAME_SYMBOLS > $AARCH_ARCHIVE_SUM_SYMBOLS
shasum -a 256 $AARCH_DMG_NAME_JDK > $AARCH_DMG_SUM_JDK
shasum -a 256 $AARCH_DMG_NAME_JRE > $AARCH_DMG_SUM_JRE

python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_ARCHIVE_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_ARCHIVE_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_ARCHIVE_NAME_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_ARCHIVE_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_ARCHIVE_SUM_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_ARCHIVE_SUM_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_DMG_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_DMG_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_DMG_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${INTEL_DMG_SUM_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_ARCHIVE_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_ARCHIVE_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_ARCHIVE_NAME_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_ARCHIVE_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_ARCHIVE_SUM_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_ARCHIVE_SUM_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_DMG_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_DMG_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_DMG_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${AARCH_DMG_SUM_JRE}"

if [ "$PUBLISH_CASKS" == true ]; then
    INTEL_JDK_SHA256=`shasum -a 256 $INTEL_DMG_NAME_JDK | awk '{ print $1 }'`
    INTEL_JRE_SHA256=`shasum -a 256 $INTEL_DMG_NAME_JRE | awk '{ print $1 }'`
    AARCH_JDK_SHA256=`shasum -a 256 $AARCH_DMG_NAME_JDK | awk '{ print $1 }'`
    AARCH_JRE_SHA256=`shasum -a 256 $AARCH_DMG_NAME_JRE | awk '{ print $1 }'`

    python3 SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $INTEL_JDK_SHA256 --aarchsha256sum $AARCH_JDK_SHA256 -i jdk
    python3 SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $INTEL_JRE_SHA256 --aarchsha256sum $AARCH_JRE_SHA256 -i jre
fi
