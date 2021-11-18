#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/async-profiler"

git config user.name SAPMACHINE_GIT_USER
git config user.email SAPMACHINE_GIT_EMAIL

git checkout master
git pull
git remote -v
#REMOTE=$(git remote -v | grep 'upstream\thttps://github.com/jvm-profiling-tools/async-profiler.git')
if [[ -z $REMOTE ]] ; then
  git remote add upstream https://github.com/jvm-profiling-tools/async-profiler.git
fi
git fetch upstream
git checkout master
git merge --no-edit upstream/master
git push --follow-tags origin master
