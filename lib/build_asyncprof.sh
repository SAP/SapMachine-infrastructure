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

cd "${WORKSPACE}/async-profiler"

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

if [ -z $BOOT_JDK ]; then
  # error
  echo "No boot JDK specified!"
  exit 1
fi

if [[ $UNAME == Darwin ]]; then
 # in case xcode11 or xcode12 devkit is present, use it
 DEVKIT_DIR_11="/jenkins/devkit/xcode11"
 DEVKIT_DIR_12="/jenkins/devkit/xcode12"
 _CONFIGURE_OS_OPTIONS="--with-macosx-bundle-name-base=SapMachine --with-macosx-bundle-id-base=com.sap.openjdk"
 if [ -d $DEVKIT_DIR_12 ]; then
   _CONFIGURE_OS_OPTIONS+=" --with-devkit=$DEVKIT_DIR_12"
 else
  if [ -d $DEVKIT_DIR_11 ]; then
   _CONFIGURE_OS_OPTIONS+=" --with-devkit=$DEVKIT_DIR_11"
  fi
 fi
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

export JAVA_HOME=${BUILD_JDK}

make all

