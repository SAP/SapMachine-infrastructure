#!/bin/bash
set -ex

if [[ -z "$GITHUB_API_ACCESS_TOKEN" ]]; then
  echo "Missing mandatory environment variable GITHUB_API_ACCESS_TOKEN"
  exit 1
fi

if [[ $1 == "-m" ]]; then
  HG=" hg"
  REPO=$2
  REPO_URL="http://hg.openjdk.java.net/"
else
  HG=""
  REPO=$1
  REPO_URL="https://github.com/"
fi

SAPMACHINE_GIT_REPOSITORY="https://SapMachine:${GITHUB_API_ACCESS_TOKEN}@github.com/SAP/SapMachine.git"

REPO_PATH="$(basename $REPO)"

cd $WORKSPACE

# modify/uncomment to clean up workspace
#if [[ $REPO_PATH == "jdk11u" ]]; then
#  rm -rf jdk11u
#fi

if [ ! -d $REPO_PATH ]; then
  git $HG clone "$REPO_URL$REPO" $REPO_PATH
  cd $REPO_PATH
  git remote add sapmachine $SAPMACHINE_GIT_REPOSITORY
  git checkout -b "$REPO"
else
  cd $REPO_PATH
  git checkout "$REPO"
  if [[ -z $HG ]]; then
    git fetch origin
    git rebase origin/master
  else
    git $HG pull
  fi
fi

git push -u SapMachine --follow-tags "$REPO"
