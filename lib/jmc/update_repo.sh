#!/bin/bash
set -ex

if  [[ -z "$GIT_USER" ]] | [[ -z "$GIT_PASSWORD" ]]; then
  echo "Missing mandatory environment variable GIT_USER or GIT_PASSWORD"
  exit 1
fi

OPENJDK_JMC_REPOSITORY="https://github.com/openjdk/jmc.git"
SAPMACHINE_JMC_REPOSITORY="https://github.com/SAP/jmc.git"
SAPMACHINE_JMC_REPOSITORY_PUSH="https://${GIT_USER}:${GIT_PASSWORD}@github.com/SAP/jmc.git"

REPO_PATH=jmc

cd $WORKSPACE

# first checkout jmc repository, branch master and pull
if [ ! -d $REPO_PATH ]; then
  git clone -b sap "$SAPMACHINE_JMC_REPOSITORY" $REPO_PATH
  cd $REPO_PATH
  git remote add upstream $OPENJDK_JMC_REPOSITORY
  git fetch upstream
  git checkout -b master upstream/master
  git checkout -b jmc8 upstream/jmc8
else
  cd $REPO_PATH
  git fetch origin
  git fetch upstream
fi

git checkout master
git pull
git push --follow-tags $SAPMACHINE_JMC_REPOSITORY_PUSH master:master

git checkout jmc8
git pull
git push --follow-tags $SAPMACHINE_JMC_REPOSITORY_PUSH jmc8:jmc8
