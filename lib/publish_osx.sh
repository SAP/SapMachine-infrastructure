#!/bin/bash
set -ex

VERSION=$(python3 ${WORKSPACE}/SapMachine-Infrastructure/lib/get_tag_version_component.py -t $GIT_TAG_NAME)

ARCHIVE_NAME_JDK="sapmachine-jdk-${VERSION}_osx-x64_bin.tar.gz"
ARCHIVE_NAME_JRE="sapmachine-jre-${VERSION}_osx-x64_bin.tar.gz"
ARCHIVE_NAME_SYMBOLS="sapmachine-jdk-${VERSION}_osx-x64_bin-symbols.tar.gz"
DMG_NAME_JDK="sapmachine-jdk-${VERSION}_osx-x64_bin.dmg"
DMG_NAME_JRE="sapmachine-jre-${VERSION}_osx-x64_bin.dmg"

mv JDK_TGZ $ARCHIVE_NAME_JDK
mv JRE_TGZ $ARCHIVE_NAME_JRE
mv SYMBOLS $ARCHIVE_NAME_SYMBOLS
mv JDK_DMG $DMG_NAME_JDK
mv JRE_DMG $DMG_NAME_JRE

ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"
ARCHIVE_SUM_SYMBOLS="$(echo $ARCHIVE_NAME_SYMBOLS | sed 's/tar\.gz/sha256\.txt/')"
DMG_SUM_JDK="$(echo $DMG_NAME_JDK | sed 's/dmg/sha256\.dmg\.txt/')"
DMG_SUM_JRE="$(echo $DMG_NAME_JRE | sed 's/dmg/sha256\.dmg\.txt/')"

shasum -a 256 $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK
shasum -a 256 $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE
shasum -a 256 $ARCHIVE_NAME_SYMBOLS > $ARCHIVE_SUM_SYMBOLS
shasum -a 256 $DMG_NAME_JDK > $DMG_SUM_JDK
shasum -a 256 $DMG_NAME_JRE > $DMG_SUM_JRE

python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_SUM_JRE}"

if [ "$PUBLISH_CASKS" == true ]; then
    JDK_SHA256=`shasum -a 256 $DMG_NAME_JDK | awk '{ print $1 }'`
    JRE_SHA256=`shasum -a 256 $DMG_NAME_JRE | awk '{ print $1 }'`

    python3 SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $JDK_SHA256 -i jdk
    python3 SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $JRE_SHA256 -i jre
fi
