#!/bin/bash

if [ -d sapmachine ]; then
    rm -rf sapmachine;
fi

git clone -b $SAPMACHINE_GIT_BRANCH "https://$SAPMACHINE_GIT_REPO" sapmachine

if [[ ! -z $GIT_TAG_NAME ]] && [[ $GIT_TAG_NAME == sapmachine* ]]; then
  git checkout $GIT_TAG_NAME
fi
