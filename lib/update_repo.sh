#!/bin/bash
set -ex

if [[ -z "$GIT_USER" ]] || [[ -z "$GITHUB_API_ACCESS_TOKEN" ]]; then
  echo "Missing mandatory environment variables GIT_USER or GITHUB_API_ACCESS_TOKEN"
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

SAPMACHINE_GIT_REPOSITORY="https://${GIT_USER}:${GITHUB_API_ACCESS_TOKEN}@github.com/SAP/SapMachine.git"

REPO_PATH="$(basename $REPO)"

cd $WORKSPACE

# uncomment/modify to cleanup workspace
rm -rf jdk15u

if [ ! -d $REPO_PATH ]; then
  git $HG clone "$REPO_URL$REPO" $REPO_PATH
  cd $REPO_PATH
  git remote add sapmachine $SAPMACHINE_GIT_REPOSITORY
  git checkout -b "$REPO"
  #if [[ -z $HG ]]; then
  #  git branch --set-upstream-to=sapmachine/$REPO
  #fi
else
  cd $REPO_PATH
  #git remote remove sapmachine
  #if [[ ! -z $HG ]]; then
  #  git remote add sapmachine $SAPMACHINE_GIT_REPOSITORY
  #fi
  git checkout "$REPO"
  if [[ -z $HG ]]; then
    git fetch origin
    git rebase origin/master
  else
    git $HG pull
  fi
fi

git push -u sapmachine --follow-tags "$REPO"
