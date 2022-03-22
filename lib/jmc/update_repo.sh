#!/bin/bash
set -ex

if  [[ -z "$GIT_USER" ]] | [[ -z "$GIT_PASSWORD" ]]; then
  echo "Missing mandatory environment variable GIT_USER or GIT_PASSWORD"
  exit 1
fi

OPENJDK_JMC_REPOSITORY="https://github.com/openjdk/jmc.git"
SAPMACHINE_JMC_REPOSITORY="https://${GIT_USER}:${GIT_PASSWORD}@github.com/SAP/jmc.git"

REPO_PATH=jmc

cd $WORKSPACE

# first checkout jmc repository, branch master and pull
if [ ! -d $REPO_PATH ]; then
  git clone "$OPENJDK_JMC_REPOSITORY" $REPO_PATH
  cd $REPO_PATH
else
  cd $REPO_PATH
  git checkout master
  git fetch origin
  git pull
fi

git push --follow-tags $SAPMACHINE_JMC_REPOSITORY master:master

git checkout jmc8
git pull

git push --follow-tags $SAPMACHINE_JMC_REPOSITORY jmc8:jmc8
