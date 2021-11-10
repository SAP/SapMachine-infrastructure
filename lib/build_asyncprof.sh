#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
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

export JAVA_HOME=${BUILD_JDK}

make
