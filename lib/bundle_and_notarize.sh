#!/bin/bash
set -ex

# sends a notarization request and prints info and log for that request
notarize() {
  rm noutf | true
  xcrun notarytool submit $2 --keychain-profile "$KEYCHAIN_PROFILE" --output-format=json --wait "$1" | tee noutf
  rc=${PIPESTATUS[0]}
  notaryout=$(cat noutf)
  rm noutf
  echo $notaryout
  id=$(echo "$notaryout" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
  status=$(echo "$notaryout" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  echo "notarytool: submitting $1 resulted in $status (id=$id)"
  if [[ $rc -eq 0 && $status == "Accepted" ]]; then
    echo "Notarization successful."
    return 0
  else
    echo "Notarization unsuccessful. Printing Log."
    xcrun notarytool log --keychain-profile "$KEYCHAIN_PROFILE" --output-format=json $id
    return 1
  fi
}

KEYCHAIN_PROFILE=sapmachine-notarization

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/SapMachine"

cd build
cd "$(ls)"
cd bundles

JDK_NAME=$(ls *jdk-*_bin.*) || true
if [ -z $JDK_NAME ]; then
  JDK_NAME=$(ls *jdk-*_bin-debug.*)
fi
if [[ $JDK_NAME = sapmachine-* ]]; then
  SAPMACHINE_BUNDLE_PREFIX="sapmachine-"
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
if notarize "${WORKSPACE}/${ARCHIVE_NAME_JDK}" "--force"; then
  return 1
fi

DMG_NAME_JDK=$(basename ${ARCHIVE_NAME_JDK} .tar.gz)
rm -rf ${DMG_NOTARIZE_BASE}
mkdir -p ${DMG_NOTARIZE_BASE}
tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JDK}" -C ${DMG_NOTARIZE_BASE}
hdierror=0
hdiutil create -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JDK} "${WORKSPACE}/${DMG_NAME_JDK}.dmg" || hdierror=1
if [ $hdierror -ne 0 ]; then
  # We see sometimes errors like "hdiutil: create failed - Resource busy." when invoking it right after tar.
  # Let's retry after sleeping a little while.
  sleep 30
  hdiutil create -verbose -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JDK} "${WORKSPACE}/${DMG_NAME_JDK}.dmg"
fi
echo "${DMG_NAME_JDK}.dmg" > "${WORKSPACE}/jdk_dmg_name.txt"

xcrun stapler staple ${DMG_NOTARIZE_BASE}/*
rm "${WORKSPACE}/${ARCHIVE_NAME_JDK}"
tar -czf "${WORKSPACE}/${ARCHIVE_NAME_JDK}" -C ${DMG_NOTARIZE_BASE} .
if notarize "${WORKSPACE}/${DMG_NAME_JDK}.dmg"; then
  return 1
fi

xcrun stapler staple "${WORKSPACE}/${DMG_NAME_JDK}.dmg"

# JRE
if notarize "${WORKSPACE}/${ARCHIVE_NAME_JRE}" "--force"; then
  return 1
fi

DMG_NAME_JRE=$(basename ${ARCHIVE_NAME_JRE} .tar.gz)
rm -rf ${DMG_NOTARIZE_BASE}
mkdir -p ${DMG_NOTARIZE_BASE}
tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JRE}" -C ${DMG_NOTARIZE_BASE}
hdierror=0
hdiutil create -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JRE} "${WORKSPACE}/${DMG_NAME_JRE}.dmg" || hdierror=1
if [ $hdierror -ne 0 ]; then
  # We see sometimes errors like "hdiutil: create failed - Resource busy." when invoking it right after tar.
  # Let's retry after sleeping a little while.
  sleep 30
  hdiutil create -verbose -srcfolder ${DMG_NOTARIZE_BASE} -fs HFS+ -volname ${DMG_NAME_JRE} "${WORKSPACE}/${DMG_NAME_JRE}.dmg"
fi
echo "${DMG_NAME_JRE}.dmg" > "${WORKSPACE}/jre_dmg_name.txt"

# Notarize if doing a release build
xcrun stapler staple ${DMG_NOTARIZE_BASE}/*
rm "${WORKSPACE}/${ARCHIVE_NAME_JRE}"
tar -czf "${WORKSPACE}/${ARCHIVE_NAME_JRE}" -C ${DMG_NOTARIZE_BASE} .
if notarize "${WORKSPACE}/${DMG_NAME_JRE}.dmg"; then
  return 1
fi
xcrun stapler staple "${WORKSPACE}/${DMG_NAME_JRE}.dmg"
