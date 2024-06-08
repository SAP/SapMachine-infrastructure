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
if [[ $REPO == "openjdk/jdk" ]]; then
  if [ ! -d $REPO_PATH ]; then
    git clone "$REPO_URL$REPO" $REPO_PATH
    cd $REPO_PATH
    git checkout -b "$REPO"
    git push --follow-tags $SAPMACHINE_GIT_REPOSITORY "$REPO"
    git checkout -b "openjdk/jdk23" jdk23
    git push --follow-tags $SAPMACHINE_GIT_REPOSITORY "openjdk/jdk23"
  else
    cd $REPO_PATH
    git checkout "$REPO"
    git fetch origin
    git remote prune origin
    git rebase origin/master
    git push --follow-tags $SAPMACHINE_GIT_REPOSITORY "$REPO"
    if git show-ref --verify --quiet refs/heads/openjdk/jdk23; then
      git checkout "openjdk/jdk23"
      git rebase origin/jdk23
    else
      git checkout -b "openjdk/jdk23" jdk23
    fi
    git push --follow-tags $SAPMACHINE_GIT_REPOSITORY "openjdk/jdk23"
  fi
else
  if [ ! -d $REPO_PATH ]; then
    git clone "$REPO_URL$REPO" $REPO_PATH
    cd $REPO_PATH
    git checkout -b "$REPO"
  else
    cd $REPO_PATH
    git checkout "$REPO"
    git fetch origin
    git remote prune origin
    git rebase origin/master
  fi
  git push --follow-tags $SAPMACHINE_GIT_REPOSITORY "$REPO"
fi
