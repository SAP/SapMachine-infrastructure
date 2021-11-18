#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/async-profiler"

git checkout master
git pull
git remote add upstream https://github.com/jvm-profiling-tools/async-profiler.git || true
git fetch upstream
git checkout master
git merge --no-edit upstream/master
git push --follow-tags origin master
