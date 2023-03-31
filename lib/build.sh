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

GTEST_DIR="${WORKSPACE}/gtest"
export GTEST_DIR

cd "${WORKSPACE}/SapMachine"

git config user.name SAPMACHINE_GIT_USER
git config user.email SAPMACHINE_GIT_EMAIL

echo "Git Revision=$(git rev-parse HEAD)"

if [ "$GITHUB_PR_NUMBER" ]; then
  git fetch $SAPMACHINE_GIT_REPOSITORY "pull/$GITHUB_PR_NUMBER/head"
  git merge FETCH_HEAD
fi

if [ -z $BOOT_JDK ]; then
  # error
  echo "No boot JDK specified!"
  exit 1
fi

# use a devkit, if set
if [ ! -z $DEVKIT_PATH ]; then
  _DEVKIT_OPTION="--with-devkit=$DEVKIT_PATH"
fi

if [[ $UNAME == Darwin ]]; then
  _CONFIGURE_OS_OPTIONS="--with-macosx-bundle-name-base=SapMachine --with-macosx-bundle-id-base=com.sap.openjdk"
fi
if [[ $UNAME == CYGWIN* ]]; then
  _CONFIGURE_OS_OPTIONS="--with-jdk-rc-name=SapMachine --with-external-symbols-in-bundles=public"
fi

if [[ ! -z $SAPMACHINE_VERSION ]]; then
  _GIT_TAG=" -t $SAPMACHINE_VERSION"
fi
if [[ ! -z $JDK_BUILD ]]; then
  _JDK_BUILD=" -b $JDK_BUILD"
fi

# need to do the python call first and the eval in a second step to bail out on $? != 0
_CONFIGURE_OPTS=$(python3 ../SapMachine-infrastructure/lib/get_configure_opts.py $_GIT_TAG $_JDK_BUILD)
eval _CONFIGURE_OPTS=(${_CONFIGURE_OPTS})

(set -x &&
bash ./configure \
--with-boot-jdk=$BOOT_JDK \
"${_CONFIGURE_OPTS[@]}" \
$_DEVKIT_OPTION \
$_CONFIGURE_OS_OPTIONS \
--disable-dtrace \
--with-freetype=bundled \
$EXTRA_CONFIGURE_OPTIONS)

(set -x && make JOBS=12 product-bundles legacy-bundles test-image)

if [[ -f ${WORKSPACE}/test.zip ]]; then
  rm "${WORKSPACE}/test.zip"
fi

zip -rq "${WORKSPACE}/test.zip" test
zip -rq "${WORKSPACE}/test.zip" make/data/blockedcertsconverter || true
zip -rq "${WORKSPACE}/test.zip" make/data/lsrdata || true
zip -rq "${WORKSPACE}/test.zip" make/data/publicsuffixlist/VERSION || true
zip -rq "${WORKSPACE}/test.zip" make/data/tzdata || true
zip -rq "${WORKSPACE}/test.zip" make/data/unicodedata || true
zip -rq "${WORKSPACE}/test.zip" make/jdk/src/classes/build/tools/makejavasecurity || true
zip -rq "${WORKSPACE}/test.zip" src/*/*/legal/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/javax/security/auth/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/sun/security/provider/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/sun/security/tools/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/data/blockedcertsconverter/blocked.certs.pem || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/data/currency/CurrencyData.properties || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/data/lsrdata/language-subtag-registry.txt || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/data/publicsuffixlist/VERSION || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/data/tzdata || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/data/unicodedata || true
zip -rq "${WORKSPACE}/test.zip" src/java.compiler/share/classes/javax/tools/snippet-files/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.smartcardio/unix/native/libj2pcsc/MUSCLE/pcsclite.h || true
zip -rq "${WORKSPACE}/test.zip" src/java.xml.crypto/share/classes/org/jcp/xml/dsig/internal/dom/XMLDSigRI.java || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.compiler/share/data/symbols/include.list || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.crypto.cryptoki/share/classes/sun/security/pkcs11/SunPKCS11.java || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.jartool/share/classes/sun/security/tools/jarsigner/Main.java || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.javadoc/share/classes/jdk/javadoc/doclet/ || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.javadoc/share/classes/jdk/javadoc/internal/doclets/formats/html/resources/script-dir || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.javadoc/share/man || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.jpackage/*/classes/jdk/jpackage/internal || true
zip -rq "${WORKSPACE}/test.zip" src/jdk.security.auth/share/classes/com/sun/security/auth/ || true

cd build
cd "$(ls)"

# get java.vm.version property into a file
echo "public class PropertyPrinter{public static void main(String[] args){System.out.print(System.getProperty(\"java.vm.version\"));}}" > PropertyPrinter.java
images/jdk/bin/java PropertyPrinter.java > ${WORKSPACE}/javavmversion.txt
rm PropertyPrinter.java

zip -rq "${WORKSPACE}/test.zip" spec.gmk
zip -rq "${WORKSPACE}/test.zip" images/jdk/release
zip -rq "${WORKSPACE}/test.zip" bundles/*jdk-*_bin.* bundles/*jdk-*_bin-debug.*

cd images

zip -rq "${WORKSPACE}/test.zip" test

cd ../bundles

JDK_NAME=$(ls *jdk-*_bin.*) || true
if [ -z $JDK_NAME ]; then
  JDK_NAME=$(ls *jdk-*_bin-debug.*)
fi
if [[ $JDK_NAME = sapmachine-* ]]; then
  SAPMACHINE_BUNDLE_PREFIX="sapmachine-"
fi
read JDK_VERSION JDK_SUFFIX<<< $(echo $JDK_NAME | sed $SEDFLAGS 's/'"${SAPMACHINE_BUNDLE_PREFIX}"'jdk-([0-9]+((\.[0-9]+))*)(.*)/ \1 \4 /p')
JDK_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jdk-${JDK_VERSION}${JDK_SUFFIX}"
JRE_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jre-${JDK_VERSION}${JDK_SUFFIX}"
SYMBOLS_BUNDLE_NAME=$(ls *_bin-*symbols.*)

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
  # substitute build number +xx to .xx to avoid problems with uploads. + is no good character :-)
  ARCHIVE_NAME_JDK="$(echo $JDK_BUNDLE_NAME | sed 's/\+/\./')"
  ARCHIVE_NAME_JRE="$(echo $JRE_BUNDLE_NAME | sed 's/\+/\./')"
  ARCHIVE_NAME_SYMBOLS="$(echo $SYMBOLS_BUNDLE_NAME | sed 's/\+/\./')"
fi

if [ "$JDK_BUNDLE_NAME" != "$ARCHIVE_NAME_JDK" ]; then
  mv "${WORKSPACE}/${JDK_BUNDLE_NAME}" "${WORKSPACE}/${ARCHIVE_NAME_JDK}"
fi

if [ "$JRE_BUNDLE_NAME" != "$ARCHIVE_NAME_JRE" ]; then
  mv "${WORKSPACE}/${JRE_BUNDLE_NAME}" "${WORKSPACE}/${ARCHIVE_NAME_JRE}"
fi

if [ "$SYMBOLS_BUNDLE_NAME" != "$ARCHIVE_NAME_SYMBOLS" ]; then
  mv "${WORKSPACE}/${SYMBOLS_BUNDLE_NAME}" "${WORKSPACE}/${ARCHIVE_NAME_SYMBOLS}"
fi

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
  hdierror=0
  hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME} "${WORKSPACE}/${DMG_NAME}.dmg" || hdierror=1
  if [ $hdierror -ne 0 ]; then
    # We see sometimes errors like "hdiutil: create failed - Resource busy." when invoking it right after tar.
    # Let's retry after sleeping a little while.
    sleep 30s
    hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME} "${WORKSPACE}/${DMG_NAME}.dmg"
  fi

  echo "${DMG_NAME}.dmg" > "${WORKSPACE}/jdk_dmg_name.txt"

  # jre
  DMG_NAME=$(basename ${ARCHIVE_NAME_JRE} .tar.gz)
  rm -rf ${DMG_BASE}
  mkdir -p ${DMG_BASE}
  tar -xzf "${WORKSPACE}/${ARCHIVE_NAME_JRE}" -C ${DMG_BASE}
  hdierror=0
  hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME} "${WORKSPACE}/${DMG_NAME}.dmg" || hdierror=1
  if [ $hdierror -ne 0 ]; then
    # We see sometimes errors like "hdiutil: create failed - Resource busy." when invoking it right after tar.
    # Let's retry after sleeping a little while.
    sleep 30s
    hdiutil create -srcfolder ${DMG_BASE} -fs HFS+ -volname ${DMG_NAME} "${WORKSPACE}/${DMG_NAME}.dmg"
  fi
  echo "${DMG_NAME}.dmg" > "${WORKSPACE}/jre_dmg_name.txt"
fi
