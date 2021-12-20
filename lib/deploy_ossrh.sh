#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/SapMachine"

git config user.name SAPMACHINE_GIT_USER
git config user.email SAPMACHINE_GIT_EMAIL

GIT_REVISION=$(git rev-parse HEAD)
echo "Git Revision=${GIT_REVISION}"

