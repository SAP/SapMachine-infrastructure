#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/async-profiler"

git config --global user.name 'SapMachine'
git config --global user.email 'sapmachine@sap.com'

git checkout master
git remote remove origin
git remote add origin https://${GITHUB_API_ACCESS_TOKEN}@github.com/SAP/async-profiler.git
git pull origin master
git remote add upstream https://github.com/jvm-profiling-tools/async-profiler.git || true
git fetch upstream
git checkout master
git merge --no-edit upstream/master
git push --follow-tags origin master
