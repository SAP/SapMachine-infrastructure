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

cd "${WORKSPACE}/async-profiler"

TARGET_DIR="async-profiler-${VERSION}-${PLATFORM}"

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

make all

rm -rf ${TARGET_DIR} ${TARGET_DIR}.tar.gz ${TARGET_DIR}.zip
mkdir ${TARGET_DIR}
cp -r build CHANGELOG.md LICENSE profiler.sh README.md ${TARGET_DIR}
if [[ $UNAME == "Linux" ]]; then
  tar czf ${TARGET_DIR}.tar.gz ${TARGET_DIR}
  echo "async-profiler/${TARGET_DIR}.tar.gz" >artifact.txt
else
  zip -r -y ${TARGET_DIR}.zip ${TARGET_DIR}
  echo "async-profiler/${TARGET_DIR}.zip" >artifact.txt
fi
