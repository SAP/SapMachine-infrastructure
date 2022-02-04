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

if [[ $JOB_NAME =~ .*linux_ppc64l.e* ]]; then PLATFORM="linux-ppc64le" ; fi
if [[ $JOB_NAME =~ .*linux_x86_64.* ]]; then PLATFORM="linux-x64" ; fi
if [[ $JOB_NAME =~ .*linux_aarch64.* ]]; then PLATFORM="linux-aarch64" ; fi
if [[ $JOB_NAME =~ .*macos.* ]]; then PLATFORM="macos" ; fi

cd "${WORKSPACE}/jmc"

TARGET_DIR="jmc-${VERSION}-${PLATFORM}"

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

find target/products -maxdepth 1 -not -type d