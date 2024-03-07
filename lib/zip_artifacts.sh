#!/bin/bash
#set -ex
set -e
shopt -s nullglob

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

cd "${WORKSPACE}/SapMachine"

echo "Creating test and jdk zip archives..."

if [[ -f ${WORKSPACE}/test.zip ]]; then
  rm "${WORKSPACE}/test.zip"
fi
if [[ -f ${WORKSPACE}/jdk.zip ]]; then
  rm "${WORKSPACE}/jdk.zip"
fi

zip -rq "${WORKSPACE}/test.zip" test
if [[ -e make/data/blockedcertsconverter ]]; then
  zip -rq "${WORKSPACE}/test.zip" make/data/blockedcertsconverter || true
fi
if [[ -e make/data/lsrdata ]]; then
  zip -rq "${WORKSPACE}/test.zip" make/data/lsrdata || true
fi
if [[ -e make/data/publicsuffixlist/VERSION ]]; then
  zip -rq "${WORKSPACE}/test.zip" make/data/publicsuffixlist/VERSION || true
fi
if [[ -e make/data/tzdata ]]; then
  zip -rq "${WORKSPACE}/test.zip" make/data/tzdata || true
fi
if [[ -e make/data/unicodedata ]]; then
  zip -rq "${WORKSPACE}/test.zip" make/data/unicodedata || true
fi
zip -rq "${WORKSPACE}/test.zip" make/data/charsetmapping || true
zip -rq "${WORKSPACE}/test.zip" make/jdk/src/classes/build/tools/makejavasecurity || true
zip -rq "${WORKSPACE}/test.zip" src/*/*/legal/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/javax/security/auth/ || true
zip -rq "${WORKSPACE}/test.zip" src/java.base/share/classes/java/lang/ || true
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
zip -rq "${WORKSPACE}/test.zip" src/jdk.javadoc/share/classes/jdk/javadoc/internal/doclets/formats/html/resources || true
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
zip -rq "${WORKSPACE}/jdk.zip" spec.gmk
zip -rq "${WORKSPACE}/test.zip" images/jdk/release

cd images

zip -rq "${WORKSPACE}/test.zip" test

cd jdk

zip -rq "${WORKSPACE}/jdk.zip" .

echo "Processing bundles..."

cd ../../bundles

JDK_NAME=$(find . \( -name "*jdk-*_bin.*" -o -name "*jdk-*_bin-debug.*" \) -exec basename {} \;)
if [[ $JDK_NAME = sapmachine-* ]]; then
  SAPMACHINE_BUNDLE_PREFIX=sapmachine-
fi
read JDK_VERSION JDK_SUFFIX<<< $(echo $JDK_NAME | sed $SEDFLAGS 's/'"${SAPMACHINE_BUNDLE_PREFIX}"'jdk-([0-9]+((\.[0-9]+))*)(.*)/ \1 \4 /p')
JDK_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jdk-${JDK_VERSION}${JDK_SUFFIX}"
JRE_BUNDLE_NAME="${SAPMACHINE_BUNDLE_PREFIX}jre-${JDK_VERSION}${JDK_SUFFIX}"
SYMBOLS_BUNDLE_NAME=$(ls *_bin-*symbols.*)

for file in "${WORKSPACE}/${SAPMACHINE_BUNDLE_PREFIX}jdk-"* "${WORKSPACE}/${SAPMACHINE_BUNDLE_PREFIX}jre-"*; do
  rm "$file"
done

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
