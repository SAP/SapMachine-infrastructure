#!/bin/bash
set -ex

read VERSION VERSION_PART VERSION_MAJOR VERSION_BUILD_NUMBER SAPMACHINE_VERSION VERSION_OS_EXT<<< $(python ${WORKSPACE}/SapMachine-Infrastructure/lib/get_tag_version_components.py -t $GIT_TAG_NAME)

ARCHIVE_NAME_JDK="sapmachine-jdk-${VERSION}_osx-x64_bin.tar.gz"
ARCHIVE_NAME_JRE="sapmachine-jre-${VERSION}_osx-x64_bin.tar.gz"
ARCHIVE_NAME_SYMBOLS="sapmachine-jdk-${VERSION}_osx-x64_bin-symbols.tar.gz"

mv JDK $ARCHIVE_NAME_JDK
mv JRE $ARCHIVE_NAME_JRE
mv SYMBOLS $ARCHIVE_NAME_SYMBOLS

# create dmg
DMG_BASE="${WORKSPACE}/dmg_base"
# jdk
DMG_NAME_JDK=$(basename ${ARCHIVE_NAME_JDK} .tar.gz)
rm -rf ${DMG_BASE}
mkdir -p ${DMG_BASE}
tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JDK}" -C ${DMG_BASE}
hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME_JDK} "${WORKSPACE}/${DMG_NAME_JDK}.dmg"

# jre
DMG_NAME_JRE=$(basename ${ARCHIVE_NAME_JRE} .tar.gz)
rm -rf ${DMG_BASE}
mkdir -p ${DMG_BASE}
tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JRE}" -C ${DMG_BASE}
hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME_JRE} "${WORKSPACE}/${DMG_NAME_JRE}.dmg"

DMG_NAME_JDK="${DMG_NAME_JDK}.dmg"
DMG_NAME_JRE="${DMG_NAME_JRE}.dmg"

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

python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JDK}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JRE}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_SYMBOLS}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JDK}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JRE}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_SYMBOLS}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_NAME_JDK}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_NAME_JRE}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_SUM_JDK}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_SUM_JRE}"

if [ "$PUBLISH_CASKS" == true ]; then
    JDK_SHA256=`shasum -a 256 $DMG_NAME_JDK | awk '{ print $1 }'`
    JRE_SHA256=`shasum -a 256 $DMG_NAME_JRE | awk '{ print $1 }'`

    python SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $JDK_SHA256 -i jdk
    python SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $JRE_SHA256 -i jre
fi
