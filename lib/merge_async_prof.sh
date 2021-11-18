#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

git config user.name SAPMACHINE_GIT_USER
git config user.email SAPMACHINE_GIT_EMAIL

cd "${WORKSPACE}/async-profiler"

git pull
git remote add upstream https://github.com/jvm-profiling-tools/async-profiler.git
git fetch upstream
git checkout master
git merge --no-edit upstream/master
git push --follow-tags origin master 2>../push.out
