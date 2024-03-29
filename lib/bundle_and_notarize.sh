#!/bin/bash
#set -ex
set -e

# Send notarization request and wait for completion. If unsuccessful, print request log and exit with error.
KEYCHAIN_PROFILE=sapmachine-notarization
notarize() {
  notaryout=$(set -x && xcrun notarytool submit $2 --keychain-profile "$KEYCHAIN_PROFILE" --output-format=json --wait "$1")
  rc=$?
  echo $notaryout
  id=$(echo "$notaryout" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
  status=$(echo "$notaryout" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  if [[ $rc -eq 0 && $status == "Accepted" ]]; then
    echo "Notarization result for $1: $status (rc=$rc, id=$id)"
  else
    echo "Notarization of $1 failed: $status (rc=$rc, id=$id). Printing Log and exiting."
    xcrun notarytool log --keychain-profile "$KEYCHAIN_PROFILE" --output-format=json $id
    exit 1
  fi
}

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/SapMachine/build"
cd "$(ls)/bundles"

JDK_NAME=$(find . \( -name "*jdk-*_bin.*" -o -name "*jdk-*_bin-debug.*" \) -exec basename {} \;)
if [[ $JDK_NAME = sapmachine-* ]]; then
  SAPMACHINE_BUNDLE_PREFIX=sapmachine-
fi
read JDK_VERSION JDK_SUFFIX<<< $(echo $JDK_NAME | sed -En 's/'"${SAPMACHINE_BUNDLE_PREFIX}"'jdk-([0-9]+((\.[0-9]+))*)(.*)/ \1 \4 /p')
JDK_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jdk-${JDK_VERSION}${JDK_SUFFIX}"
JRE_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jre-${JDK_VERSION}${JDK_SUFFIX}"
SYMBOLS_BUNDLE_NAME=$(ls *_bin-*symbols.*)

if [ "$RELEASE" == true ]; then
  # remove build number +xx from release build filenames
  ARCHIVE_NAME_JDK="$(echo $JDK_BUNDLE_NAME | sed 's/\+[0-9]*//')"
  ARCHIVE_NAME_JRE="$(echo $JRE_BUNDLE_NAME | sed 's/\+[0-9]*//')"
  ARCHIVE_NAME_SYMBOLS="$(echo $SYMBOLS_BUNDLE_NAME | sed 's/\+[0-9]*//')"
else
  # substitute build number +xx to .xx to avoid problems with uploads. + is no good character :-)
  ARCHIVE_NAME_JDK="$(echo $JDK_BUNDLE_NAME | sed 's/\+/\./')"
  ARCHIVE_NAME_JRE="$(echo $JRE_BUNDLE_NAME | sed 's/\+/\./')"
  ARCHIVE_NAME_SYMBOLS="$(echo $SYMBOLS_BUNDLE_NAME | sed 's/\+/\./')"
fi

# Prepare
rm -rf *.dmg
DMG_NOTARIZE_BASE="${WORKSPACE}/dmg_notarize_base"
security unlock-keychain -p $unlockpass ~/Library/Keychains/login.keychain

# JDK
notarize "${WORKSPACE}/${ARCHIVE_NAME_JDK}" "--force"
DMG_NAME_JDK=$(basename ${ARCHIVE_NAME_JDK} .tar.gz)
rm -rf ${DMG_NOTARIZE_BASE}
mkdir -p ${DMG_NOTARIZE_BASE}
tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JDK}" -C ${DMG_NOTARIZE_BASE}
(set -x && hdiutil create -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JDK} "${WORKSPACE}/${DMG_NAME_JDK}.dmg" || return 1)
if [ $? -ne 0 ]; then
  # Sometimes we see errors like "hdiutil: create failed - Resource busy." Let's retry once after sleeping a little while.
  sleep 30
  (set -x && hdiutil create -verbose -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JDK} "${WORKSPACE}/${DMG_NAME_JDK}.dmg")
fi
echo "${DMG_NAME_JDK}.dmg" > "${WORKSPACE}/jdk_dmg_name.txt"
xcrun stapler staple ${DMG_NOTARIZE_BASE}/*
rm "${WORKSPACE}/${ARCHIVE_NAME_JDK}"
tar -czf "${WORKSPACE}/${ARCHIVE_NAME_JDK}" -C ${DMG_NOTARIZE_BASE} .
notarize "${WORKSPACE}/${DMG_NAME_JDK}.dmg"
xcrun stapler staple "${WORKSPACE}/${DMG_NAME_JDK}.dmg"

# JRE
notarize "${WORKSPACE}/${ARCHIVE_NAME_JRE}" "--force"
DMG_NAME_JRE=$(basename ${ARCHIVE_NAME_JRE} .tar.gz)
rm -rf ${DMG_NOTARIZE_BASE}
mkdir -p ${DMG_NOTARIZE_BASE}
tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JRE}" -C ${DMG_NOTARIZE_BASE}
(set -x && hdiutil create -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JRE} "${WORKSPACE}/${DMG_NAME_JRE}.dmg" || return 1)
if [ $? -ne 0 ]; then
  # Sometimes we see errors like "hdiutil: create failed - Resource busy." Let's retry once after sleeping a little while.
  sleep 30
  (set -x && hdiutil create -verbose -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JRE} "${WORKSPACE}/${DMG_NAME_JRE}.dmg")
fi
echo "${DMG_NAME_JRE}.dmg" > "${WORKSPACE}/jre_dmg_name.txt"
xcrun stapler staple ${DMG_NOTARIZE_BASE}/*
rm "${WORKSPACE}/${ARCHIVE_NAME_JRE}"
tar -czf "${WORKSPACE}/${ARCHIVE_NAME_JRE}" -C ${DMG_NOTARIZE_BASE} .
notarize "${WORKSPACE}/${DMG_NAME_JRE}.dmg"
xcrun stapler staple "${WORKSPACE}/${DMG_NAME_JRE}.dmg"
