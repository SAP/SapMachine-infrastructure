#!/bin/bash
set -ex

if [ -d sapmachine ]; then
    rm -rf sapmachine;
fi

if [[ -z $SAPMACHINE_GIT_REPOSITORY ]]; then
  SAPMACHINE_GIT_REPOSITORY="https://github.com/SAP/SapMachine.git"
fi

export GIT_COMMITTER_NAME=sapmachine
export GIT_COMMITTER_EMAIL="sapmachine@sap.com"

git clone -b $SAPMACHINE_GIT_BRANCH $SAPMACHINE_GIT_REPOSITORY sapmachine

cd sapmachine

git config user.email $GIT_COMMITTER_EMAIL
git config user.name $GIT_COMMITTER_NAME

if [[ ! -z $GIT_TAG_NAME ]] && [[ $GIT_TAG_NAME == sapmachine* ]]; then
  git checkout $GIT_TAG_NAME
fi

if [ "$GITHUB_PR_NUMBER" ]; then
  git fetch origin "pull/$GITHUB_PR_NUMBER/head"
  git merge FETCH_HEAD
fi
