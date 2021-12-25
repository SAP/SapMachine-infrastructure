#!/bin/bash
set -ex

if  [[ -z "$GIT_USER" ]] | [[ -z "$GIT_PASSWORD" ]]; then
  echo "Missing mandatory environment variable GIT_USER or GIT_PASSWORD"
  exit 1
fi

REPO=$1
REPO_URL="https://github.com/"

SAPMACHINE_GIT_REPOSITORY="https://${GIT_USER}:${GIT_PASSWORD}@github.com/SAP/SapMachine.git"

REPO_PATH="$(basename $REPO)"

cd $WORKSPACE

# modify/uncomment to clean up workspace
#if [[ $REPO_PATH == "jdk11u" ]]; then
#  rm -rf $REPO_PATH
#fi

if [ ! -d $REPO_PATH ]; then
  git clone "$REPO_URL$REPO" $REPO_PATH
  cd $REPO_PATH
  git checkout -b "$REPO"
else
  cd $REPO_PATH
  git checkout "$REPO"
  git fetch origin
  git rebase origin/master
fi

git push --follow-tags $SAPMACHINE_GIT_REPOSITORY "$REPO"
