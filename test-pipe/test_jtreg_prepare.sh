#!/bin/bash

if [ -d sapmachine ]; then
    rm -rf sapmachine;
fi

git clone -b $SAPMACHINE_GIT_BRANCH "https://$SAPMACHINE_GIT_REPO" sapmachine

cd sapmachine

if [[ ! -z $GIT_TAG_NAME ]] && [[ $GIT_TAG_NAME == sapmachine* ]]; then
  git checkout $GIT_TAG_NAME
fi

if [ "$GITHUB_PR_NUMBER" ]; then
  git fetch origin "pull/$GITHUB_PR_NUMBER/head"
  git merge FETCH_HEAD
fi
