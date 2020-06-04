#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

UNAME=`uname`
if [[ $UNAME == Darwin ]]; then
    SEDFLAGS='-En'
else
    SEDFLAGS='-rn'
fi

if [[ $UNAME == CYGWIN* ]]; then
  WORKSPACE=$(cygpath -u "${WORKSPACE}")
fi

if [[ -z $NO_CHECKOUT ]]; then
  if [ -d SapMachine ]; then
      rm -rf SapMachine;
  fi

  if [[ -z $SAPMACHINE_GIT_REPOSITORY ]]; then
    SAPMACHINE_GIT_REPOSITORY="https://github.com/SAP/SapMachine.git"
  fi

  if [[ ! -z $GIT_USER && ! -z GIT_PASSWORD ]]; then
    git clone -b $SAPMACHINE_GIT_BRANCH "https://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPOSITORY" "${WORKSPACE}/SapMachine"
  else
    git clone -b $SAPMACHINE_GIT_BRANCH $SAPMACHINE_GIT_REPOSITORY "${WORKSPACE}/SapMachine"
  fi
fi

if [ -d gtest ]; then
  rm -rf gtest;
fi

GTEST_DIR="${WORKSPACE}/gtest"
export GTEST_DIR
git clone -b release-1.8.1 https://github.com/google/googletest.git $GTEST_DIR

cd "${WORKSPACE}/SapMachine"

git config user.name SAPMACHINE_GIT_USER
git config user.email SAPMACHINE_GIT_EMAIL

GIT_REVISION=$(git rev-parse HEAD)
echo "Git Revision=${GIT_REVISION}"

GTEST_RESULT_PATH="gtest_all_server"

if [[ -z $NO_CHECKOUT ]]; then
  if [ "$GITHUB_PR_NUMBER" ]; then
    git fetch origin "pull/$GITHUB_PR_NUMBER/head"
    git merge FETCH_HEAD
  fi

  if [[ ! -z $GIT_TAG_NAME ]]; then
    git checkout $GIT_TAG_NAME
  fi
fi

if [ -z $BOOT_JDK ]; then
  # error
  echo "No boot JDK specified!"
  exit 1
fi

if [[ $UNAME == Darwin ]]; then
  _CONFIGURE_OS_OPTIONS="--with-macosx-bundle-name-base=SapMachine --with-macosx-bundle-id-base=com.sap.openjdk"
fi
if [[ $UNAME == CYGWIN* ]]; then
  _CONFIGURE_OS_OPTIONS="--with-jdk-rc-name=SapMachine --with-external-symbols-in-bundles=public"
fi

if [[ ! -z $GIT_TAG_NAME ]]; then
  _GIT_TAG=" -t $GIT_TAG_NAME"
fi
if [[ ! -z $BUILD_NUMBER ]]; then
  _BUILD_NUMBER="-b $BUILD_NUMBER"
fi
if [ "$RELEASE" == true ]; then
  _RELEASE=" -r"
fi
if [[ ! -z $SAPMACHINE_GIT_BRANCH ]]; then
  _GIT_BRANCH=" -g $SAPMACHINE_GIT_BRANCH"
fi

eval _CONFIGURE_OPTS=($(python3 ../SapMachine-Infrastructure/lib/get_configure_opts.py $_GIT_TAG $_RELEASE $_BUILD_NUMBER $_GIT_BRANCH))

bash ./configure \
--with-boot-jdk=$BOOT_JDK \
"${_CONFIGURE_OPTS[@]}" \
$_CONFIGURE_OS_OPTIONS \
--with-freetype=bundled \
$_CONFIGURE_SYSROOT \
$EXTRA_CONFIGURE_OPTIONS

# try to build with legacy-bundles in one step
legacy_bundles_available=1
make JOBS=12 product-bundles legacy-bundles test-image || true

# In case there was an error, we give it another try without legacy bundles
# and try to create the legacy bundle manually afterwards.
# This is needed to support building older source versions that didn't have
# the legacy-bundles target.
# Drawback: If there is a real build error, we'll restart the build and run
# into it again.
if [ ${PIPESTATUS[0]} -ne 0 ]; then
  legacy_bundles_available=0
  make JOBS=12 product-bundles test-image
fi

if [ $legacy_bundles_available -ne 1 ]; then
  if [[ $UNAME == Darwin ]]; then
    make JOBS=12 mac-legacy-jre-bundle || true
  else
    make JOBS=12 legacy-jre-image || true
  fi
fi

make run-test-gtest

rm "${WORKSPACE}/test.zip" || true
zip -rq "${WORKSPACE}/test.zip" test
zip -rq "${WORKSPACE}/test.zip" make/data/lsrdata
zip -rq "${WORKSPACE}/test.zip" make/data/blacklistedcertsconverter/blacklisted.certs.pem || true
zip -rq "${WORKSPACE}/test.zip" make/data/unicodedata || true
zip -rq "${WORKSPACE}/test.zip" make/data/tzdata || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.incubator.jpackage/windows/classes/jdk/incubator/jpackage/internal || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.incubator.jpackage/linux/classes/jdk/incubator/jpackage/internal || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.incubator.jpackage/macosx/classes/jdk/incubator/jpackage/internal || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/javax/security/auth/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/sun/security/provider/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/sun/security/tools/ || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.crypto.cryptoki/share/classes/sun/security/pkcs11/SunPKCS11.java || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.jartool/share/classes/sun/security/tools/jarsigner/Main.java || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.security.auth/share/classes/com/sun/security/auth/ || true

cd "${WORKSPACE}/SapMachine/build"
cd "$(ls)"
zip -rq ${WORKSPACE}/support_gensrc.zip support/gensrc
zip -rq ${WORKSPACE}/test.zip spec.gmk
zip -rq ${WORKSPACE}/test.zip bundles/*jdk-*_bin.*
cd images
zip -rq ${WORKSPACE}/test.zip test

cd ../bundles

if [ "$(ls sapmachine-jdk-*_bin.* | wc -l)" -gt "0" ]; then
  SAPMACHINE_BUNDLE_PREFIX="sapmachine-"
fi

JDK_NAME=$(ls ${SAPMACHINE_BUNDLE_PREFIX}jdk-*_bin.*)
read JDK_MAJOR JDK_SUFFIX<<< $(echo $JDK_NAME | sed $SEDFLAGS 's/'"${SAPMACHINE_BUNDLE_PREFIX}"'jdk-([0-9]+((\.[0-9]+))*)(.*)/ \1 \4 /p')
JDK_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jdk-${JDK_MAJOR}${JDK_SUFFIX}"
JRE_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jre-${JDK_MAJOR}${JDK_SUFFIX}"
SYMBOLS_BUNDLE_NAME=$(ls ${SAPMACHINE_BUNDLE_PREFIX}*_bin-symbols.*)

if [ $legacy_bundles_available -ne 1 ]; then
  HAS_JRE=$(ls ${SAPMACHINE_BUNDLE_PREFIX}jre* | wc -l)

  if [ "$HAS_JRE" -lt "1" ]; then
    JRE_BUNDLE_TOP_DIR="${SAPMACHINE_BUNDLE_PREFIX}jre-$JDK_MAJOR.jre"

    rm -rf $JRE_BUNDLE_NAME
    mkdir $JRE_BUNDLE_TOP_DIR
    if [[ $UNAME == Darwin ]]; then
        cp -a ../images/${SAPMACHINE_BUNDLE_PREFIX}jre-bundle/$JRE_BUNDLE_TOP_DIR* .
        SetFile -a b ${SAPMACHINE_BUNDLE_PREFIX}jre*
    else
        cp -r ../images/jre/* $JRE_BUNDLE_TOP_DIR
    fi
    find $JRE_BUNDLE_TOP_DIR -name "*.debuginfo" -type f -delete

    if [ ${JDK_SUFFIX: -4} == ".zip" ]; then
      zip -r $JRE_BUNDLE_NAME $JRE_BUNDLE_TOP_DIR
    else
      tar -czf  $JRE_BUNDLE_NAME $JRE_BUNDLE_TOP_DIR
    fi

    rm -rf $JRE_BUNDLE_TOP_DIR
  fi
fi

rm "${WORKSPACE}/${SAPMACHINE_BUNDLE_PREFIX}jdk-*" || true
rm "${WORKSPACE}/${SAPMACHINE_BUNDLE_PREFIX}jre-*" || true

cp ${JDK_BUNDLE_NAME} "${WORKSPACE}"
cp ${JRE_BUNDLE_NAME} "${WORKSPACE}"
cp ${SYMBOLS_BUNDLE_NAME} "${WORKSPACE}"

if [ "$RELEASE" == true ]; then
  # remove build number +xx from release build filenames
  ARCHIVE_NAME_JDK="$(echo $JDK_BUNDLE_NAME | sed 's/\+[0-9]*//')"
  ARCHIVE_NAME_JRE="$(echo $JRE_BUNDLE_NAME | sed 's/\+[0-9]*//')"
  ARCHIVE_NAME_SYMBOLS="$(echo $SYMBOLS_BUNDLE_NAME | sed 's/\+[0-9]*//')"
else
  # substitute build number +xx to .xx to avoid problmes with uploads. + is no good character :-)
  ARCHIVE_NAME_JDK="$(echo $JDK_BUNDLE_NAME | sed 's/\+/\./')"
  ARCHIVE_NAME_JRE="$(echo $JRE_BUNDLE_NAME | sed 's/\+/\./')"
  ARCHIVE_NAME_SYMBOLS="$(echo $SYMBOLS_BUNDLE_NAME | sed 's/\+/\./')"
fi

mv "${WORKSPACE}/${JDK_BUNDLE_NAME}" "${WORKSPACE}/${ARCHIVE_NAME_JDK}"
mv "${WORKSPACE}/${JRE_BUNDLE_NAME}" "${WORKSPACE}/${ARCHIVE_NAME_JRE}"
mv "${WORKSPACE}/${SYMBOLS_BUNDLE_NAME}" "${WORKSPACE}/${ARCHIVE_NAME_SYMBOLS}"

echo "${ARCHIVE_NAME_JDK}" > "${WORKSPACE}/jdk_bundle_name.txt"
echo "${ARCHIVE_NAME_JRE}" > "${WORKSPACE}/jre_bundle_name.txt"
echo "${ARCHIVE_NAME_SYMBOLS}" > "${WORKSPACE}/symbols_bundle_name.txt"

if [[ $UNAME == Darwin ]]; then
  rm -rf *.dmg

  # create dmg
  DMG_BASE="${WORKSPACE}/dmg_base"
  # jdk
  DMG_NAME=$(basename ${ARCHIVE_NAME_JDK} .tar.gz)
  rm -rf ${DMG_BASE}
  mkdir -p ${DMG_BASE}
  tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JDK}" -C ${DMG_BASE}
  hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME} "${WORKSPACE}/${DMG_NAME}.dmg"
  echo "${DMG_NAME}.dmg" > "${WORKSPACE}/jdk_dmg_name.txt"

  # jre
  DMG_NAME=$(basename ${ARCHIVE_NAME_JRE} .tar.gz)
  rm -rf ${DMG_BASE}
  mkdir -p ${DMG_BASE}
  tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JRE}" -C ${DMG_BASE}
  hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME} "${WORKSPACE}/${DMG_NAME}.dmg"
  echo "${DMG_NAME}.dmg" > "${WORKSPACE}/jre_dmg_name.txt"
fi

cp ../test-results/$GTEST_RESULT_PATH/gtest.xml "${WORKSPACE}"
