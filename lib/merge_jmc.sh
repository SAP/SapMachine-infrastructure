#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/jmc"

git config --global user.name 'SapMachine'
git config --global user.email 'sapmachine@sap.com'

git checkout master
git remote remove origin
git remote add origin https://${GIT_PASSWORD}@github.com/SAP/jmc.git
git pull origin master
git pull origin sap
git remote add upstream https://github.com/openjdk/jmc.git || true
git fetch upstream
git checkout master
git merge --no-edit upstream/master
git checkout sap
git rebase master
git checkout sap application/org.openjdk.jmc.rcp.application/splash.bmp
git add application/org.openjdk.jmc.rcp.application/splash.bmp
git -c core.editor=true rebase continue
git push -f origin sap
git checkout master
RESULT=`git push --follow-tags origin master 2>&1`
echo $RESULT
if [[ "${RESULT}" == "Everything up-to-date" ]]; then
    exit 1
else
    exit 0
fi
