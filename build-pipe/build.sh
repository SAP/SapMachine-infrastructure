#!/bin/bash
set -ex

if [ -d SapMachine ]; then
    rm -rf SapMachine;
fi

git clone -b $SAPMACHINE_GIT_BRANCH "http://github.com/SAP/SapMachine.git" SapMachine

cd SapMachine

GIT_REVISION=$(git rev-parse HEAD)
echo "Git Revision=${GIT_REVISION}"

GTEST_RESULT_PATH="gtest_all_server"

if [ "$GITHUB_PR_NUMBER" ]; then
  git fetch origin "pull/$GITHUB_PR_NUMBER/head"
  git merge FETCH_HEAD
fi

if [[ ! -z $GIT_TAG_NAME ]]; then
  git checkout $GIT_TAG_NAME
fi

if [ -z $BOOT_JDK ]; then
  if [ -e "/opt/boot_jdk" ]; then
    BOOT_JDK="/opt/boot_jdk"
  fi
fi

VENDOR_NAME="SAP SE"
VENDOR_URL="https://sapmachine.io"
VENDOR_BUG_URL="https://github.com/SAP/SapMachine/issues/new"
VENDOR_VM_BUG_URL="https://github.com/SAP/SapMachine/issues/new"

if [[ $GIT_TAG_NAME == sapmachine-* ]]; then
  read VERSION_MAJOR VERSION_MINOR SAPMACHINE_VERSION<<< $(echo $GIT_TAG_NAME \
  | sed -rn 's/sapmachine\-([0-9]+)(\.[0-9]\.[0-9])?\+([0-9]+)\-?([0-9]*)(\-alpine)?/ \1 \3 \4 /p')

  if [[ -z $SAPMACHINE_VERSION || -z $VERSION_MAJOR || -z $VERSION_MINOR ]]; then
    # error
    echo "Invalid tag!"
    exit 1
  fi

  VERSION_PRE_OPT="ea"

  if [ "$RELEASE" == true ]; then
    if [ "$VERSION_MAJOR" == "11" ]; then
      LTS='LTS-'
    else
      LTS=''
    fi

    VERSION_PRE_OPT=''
  fi

  VERSION_DATE=$(python ../lib/get_tag_timestamp.py -t $GIT_TAG_NAME)

  if [[ -z $VERSION_DATE ]]; then
    VERSION_DATE=$(date -I -u)
  fi

  bash ./configure \
  --with-boot-jdk=$BOOT_JDK \
  --with-version-feature=$VERSION_MAJOR \
  --with-version-opt=${LTS}sapmachine-$SAPMACHINE_VERSION \
  --with-version-pre=$VERSION_PRE_OPT --with-version-build=$VERSION_MINOR \
  --with-version-date=$VERSION_DATE \
  --disable-warnings-as-errors \
  --with-vendor-name="$VENDOR_NAME" \
  --with-vendor-url="$VENDOR_URL" \
  --with-vendor-bug-url="$VENDOR_BUG_URL" \
  --with-vendor-vm-bug-url="$VENDOR_VM_BUG_URL" \
    $_CONFIGURE_SYSROOT
else
  bash ./configure \
  --with-boot-jdk=$BOOT_JDK \
  --with-version-opt=sapmachine \
  --with-version-pre=snapshot \
  --with-version-build=$BUILD_NUMBER \
  --disable-warnings-as-errors \
  --with-vendor-name="$VENDOR_NAME" \
  --with-vendor-url="$VENDOR_URL" \
  --with-vendor-bug-url="$VENDOR_BUG_URL" \
  --with-vendor-vm-bug-url="$VENDOR_VM_BUG_URL" \
    $_CONFIGURE_SYSROOT
fi

make JOBS=12 product-bundles test-image docs-zip
make JOBS=12 legacy-jre-image || true

make run-test-gtest

tar czf ../build.tar.gz build
rm ../test.zip || true
zip -rq ../test.zip test

cd build
cd "$(ls)"
zip -rq ../../../test.zip bundles/sapmachine-jdk-*_bin.*
cd images
zip -rq ../../../../test.zip test

cd ../bundles
HAS_JRE=$(ls sapmachine-jre* | wc -l)

if [ "$HAS_JRE" -lt "1" ]; then
  JDK_NAME=$(ls sapmachine-jdk-*_bin.*)
  read JDK_MAJOR JDK_SUFFIX<<< $(echo $JDK_NAME | sed -rn 's/sapmachine-jdk-([0-9]+)(.*)/ \1 \2 /p')
  JRE_BUNDLE_NAME="sapmachine-jre-${JDK_MAJOR}${JDK_SUFFIX}"
  JRE_BUNDLE_TOP_DIR="sapmachine-jre-$JDK_MAJOR"

  rm -rf $JRE_BUNDLE_NAME
  mkdir $JRE_BUNDLE_TOP_DIR
  cp -r ../images/jre/* $JRE_BUNDLE_TOP_DIR
  find $JRE_BUNDLE_TOP_DIR -name "*.debuginfo" -type f -delete

  if [ ${JDK_SUFFIX: -4} == ".zip" ]; then
    zip -r $JRE_BUNDLE_NAME $JRE_BUNDLE_TOP_DIR
  else
    tar -czf  $JRE_BUNDLE_NAME $JRE_BUNDLE_TOP_DIR
  fi

  rm -rf $JRE_BUNDLE_TOP_DIR
fi

rm ../../../../sapmachine-jdk-* || true
rm ../../../../sapmachine-jre-* || true
rm ../../../../apidocs.zip || true

ls

cp sapmachine-jdk-*_bin.* ../../../..
cp sapmachine-jre-*_bin.* ../../../..
cp *-docs.zip ../../../../apidocs.zip

cp ../test-results/$GTEST_RESULT_PATH/gtest.xml ../../../..
