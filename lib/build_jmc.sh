#!/bin/bash
set -ex

UNAME=`uname`
export PATH=$PATH:/usr/bin

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

if [[ ! -z $GIT_TAG_NAME ]]; then
  VERSION=${GIT_TAG_NAME:1:3}
else
  VERSION=snapshot
fi


cd "${WORKSPACE}/jmc"

git config user.name SAPMACHINE_GIT_USER
git config user.email SAPMACHINE_GIT_EMAIL

GIT_REVISION=$(git rev-parse HEAD)
echo "Git Revision=${GIT_REVISION}"

if [[ -z $NO_CHECKOUT ]]; then
  if [ "$GITHUB_PR_NUMBER" ]; then
    git fetch origin "pull/$GITHUB_PR_NUMBER/head"
    git merge FETCH_HEAD
  fi

  if [[ ! -z $GIT_TAG_NAME ]]; then
    git checkout $GIT_TAG_NAME
  fi
fi

export JAVA_HOME=${BUILD_JDK}

rm -fr target

./build.sh --packageJmc

if [[ $JOB_NAME =~ .*linux_x86_64.* ]]; then FILE="linux.gtk.x86_64.tar.gz" ; fi
if [[ $JOB_NAME =~ .*macos_aarch64.* ]]; then FILE="macosx.cocoa.aarch64.tar.gz" ; fi
if [[ $JOB_NAME =~ .*macos_x86_64.* ]]; then FILE="macosx.cocoa.x86_64.tar.gz" ; fi
if [[ $JOB_NAME =~ .*win.* ]]; then FILE="win32.win32.x86_64.zip" ; fi

echo "target/products/org.openjdk.jmc-$FILE" > artifact.txt