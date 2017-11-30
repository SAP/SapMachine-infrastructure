#!/bin/bash
set -ex

HG_HOST="hg.openjdk.java.net"
HG_PATH="jdk/jdk"
#HG_HOST="bitbucket.org"
#HG_PATH="axel7born/mercurial2git"

if [[ -z "$GIT_USER" ]] || [[ -z "$GIT_PASSWORD" ]]; then
    echo "Missing mandatory environment variables GIT_USER or GIT_PASSWORD"
    exit 1
fi

GIT_REPO="http://${GIT_USER}:${GIT_PASSWORD}@github.com/SAP/SapMachine"
REPO_PATH="$(basename $HG_PATH)"

echo $WORKSPACE
cd $WORKSPACE

if [ ! -d $REPO_PATH ]; then
  git hg clone "http://$HG_HOST/$HG_PATH"
  cd $REPO_PATH
  git remote add origin $GIT_REPO
  git checkout -b "$HG_PATH"
else
  cd $REPO_PATH
  git remote remove origin
  git remote add origin $GIT_REPO
  git hg pull
  git checkout "$HG_PATH"
fi

git push --tags origin "$HG_PATH"
