#!/bin/bash
set -ex

if [ -d SapMachine ]; then
    rm -rf SapMachine;
fi
export GIT_COMMITTER_NAME=$GIT_USER
export GIT_COMMITTER_EMAIL="sapmachine@sap.com"

git clone -b $SAPMACHINE_GIT_BRANCH "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine

cd SapMachine

ALPINE_OPTS=""
GTEST_RESULT_PATH="gtest_all_server"

if [[ $SAPMACHINE_GIT_BRANCH == *-alpine ]] || [[ $GIT_TAG_NAME == *-alpine ]]; then
  ALPINE_OPTS="--disable-warnings-as-errors"
  GTEST_RESULT_PATH="gtest]all]server"
fi

git config user.email $GIT_COMMITTER_EMAIL
git config user.name $GIT_USER

if [ "$GITHUB_PR_NUMBER" ]; then
  git fetch origin "pull/$GITHUB_PR_NUMBER/head"
  git merge FETCH_HEAD
fi

if [[ ! -z $GIT_TAG_NAME ]]; then
  git checkout $GIT_TAG_NAME
fi

VERSION_PRE_OPT="--with-version-pre=ea"

if [ "$RELEASE" == true ]; then
  VERSION_PRE_OPT=""
fi

VENDOR_INFO="--with-vendor-name=\'SAP SE\' --with-vendor-url=https://sapmachine.io \
--with-vendor-bug-url=https://github.com/SAP/SapMachine/issues/new \
--with-vendor-vm-bug-url=https://github.com/SAP/SapMachine/issues/new"

if [[ $GIT_TAG_NAME == sapmachine-* ]]; then
  read VERSION_MAJOR VERSION_MINOR SAPMACHINE_VERSION<<< $(echo $GIT_TAG_NAME \
  | sed -rn 's/sapmachine\-([0-9]+)\+([0-9]+)\-?([0-9]*)(\-alpine)?/ \1 \2 \3 /p')

  if [ -z $SAPMACHINE_VERSION ]; then
    bash ./configure --with-boot-jdk=$BOOT_JDK --with-version-feature=$VERSION_MAJOR \
    --with-version-opt=sapmachine \
    $VERSION_PRE_OPT --with-version-build=$VERSION_MINOR $ALPINE_OPTS \
    --with-vendor-name='SAP SE' --with-vendor-url='https://sapmachine.io' \
    --with-vendor-bug-url='https://github.com/SAP/SapMachine/issues/new' \
    --with-vendor-vm-bug-url='https://github.com/SAP/SapMachine/issues/new'
  else
    bash ./configure --with-boot-jdk=$BOOT_JDK --with-vendor-name='SAP SE' --with-version-feature=$VERSION_MAJOR \
    --with-version-opt=sapmachine-$SAPMACHINE_VERSION \
    $VERSION_PRE_OPT --with-version-build=$VERSION_MINOR $ALPINE_OPTS \
    --with-vendor-name='SAP SE' --with-vendor-url='https://sapmachine.io' \
    --with-vendor-bug-url='https://github.com/SAP/SapMachine/issues/new' \
    --with-vendor-vm-bug-url='https://github.com/SAP/SapMachine/issues/new'

  fi
else
  bash ./configure --with-boot-jdk=$BOOT_JDK --with-vendor-name='SAP SE' --with-version-opt=sapmachine \
  --with-version-pre=snapshot --with-version-build=$BUILD_NUMBER $ALPINE_OPTS \
  --with-vendor-name='SAP SE' --with-vendor-url='https://sapmachine.io' \
  --with-vendor-bug-url='https://github.com/SAP/SapMachine/issues/new' \
  --with-vendor-vm-bug-url='https://github.com/SAP/SapMachine/issues/new'
fi

make JOBS=12 product-bundles test-image docs-zip

make run-test-gtest

tar czf ../build.tar.gz build

cd build
cd "$(ls)"/bundles

rm ../../../../sapmachine-jdk-* || true
rm ../../../../sapmachine-jre-* || true
rm ../../../../apidocs.zip || true

ls

cp sapmachine-jdk-*_bin.tar.gz ../../../..
cp sapmachine-jre-*_bin.tar.gz ../../../..
cp *-docs.zip ../../../../apidocs.zip

cp ../test-results/$GTEST_RESULT_PATH/gtest.xml ../../../..
