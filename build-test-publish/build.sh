#!/bin/bash
set -ex

if [ -d SapMachine ]; then
    rm -rf SapMachine;
fi
export GIT_COMMITTER_NAME=$GIT_USER
export GIT_COMMITTER_EMAIL="sapmachine@sap.com"

git clone -b $SAPMACHINE_GIT_BRANCH "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine

cd SapMachine

git config user.email $GIT_COMMITTER_EMAIL
git config user.name $GIT_USER

if [ "$GITHUB_PR_NUMBER" ]; then
  git fetch origin "pull/$GITHUB_PR_NUMBER/head"
  git merge FETCH_HEAD
fi

if [[ ! -z $GIT_TAG_NAME ]]; then
  git checkout $GIT_TAG_NAME
fi

if [[ $GIT_TAG_NAME == sapmachine-* ]]; then
  read VERSION_MAJOR VERSION_MINOR <<< $(echo $GIT_TAG_NAME | sed -r 's/sapmachine\-([0-9]+)\+([0-9]*)/\1 \2/')
  bash ./configure --with-boot-jdk=$BOOT_JDK --with-version-string="$VERSION_MAJOR+$VERSION_MINOR" --with-version-opt="sapmachine"
else
  bash ./configure --with-boot-jdk=$BOOT_JDK --with-version-opt="sapmachine"
fi

make JOBS=12 images test-image
make run-test-gtest

tar czf ../build.tar.gz build

cd build
cd "$(ls)"/images

tar czf ../../../../"${SAPMACHINE_ARCHIVE_NAME_PREFIX}-jdk.tar.gz" jdk
tar czf ../../../../"${SAPMACHINE_ARCHIVE_NAME_PREFIX}-jre.tar.gz" jre

cp ../test-results/gtest_all_server/gtest.xml ../../../..
