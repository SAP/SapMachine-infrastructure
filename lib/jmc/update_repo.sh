#!/bin/bash
set -ex

if  [[ -z "$GIT_USER" ]] | [[ -z "$GIT_PASSWORD" ]]; then
  echo "Missing mandatory environment variable GIT_USER or GIT_PASSWORD"
  exit 1
fi

OPENJDK_JMC_REPOSITORY="https://github.com/openjdk/jmc.git"
SAPMACHINE_JMC_REPOSITORY_PUSH_URL="https://${GIT_USER}:${GIT_PASSWORD}@github.com/SAP/jmc.git"

# add upstream jmc repository and fetch it
cd jmc
git remote add upstream $OPENJDK_JMC_REPOSITORY
git fetch upstream

git checkout -b master upstream/master
git pull
git push --follow-tags $SAPMACHINE_JMC_REPOSITORY_PUSH_URL master:master

git checkout -b jmc8 upstream/jmc8
git pull
git push --follow-tags $SAPMACHINE_JMC_REPOSITORY_PUSH_URL jmc8:jmc8
