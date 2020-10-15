#!/bin/bash
set -ex

HG_HOST="hg.openjdk.java.net"
HG_PATH=$1

if [[ -z "$GIT_USER" ]] || [[ -z "$GITHUB_API_ACCESS_TOKEN" ]]; then
    echo "Missing mandatory environment variables GIT_USER or GITHUB_API_ACCESS_TOKEN"
    exit 1
fi

SAPMACHINE_GIT_REPOSITORY="https://${GIT_USER}:${GITHUB_API_ACCESS_TOKEN}@github.com/SAP/SapMachine.git"

REPO_PATH="$(basename $HG_PATH)"

echo $WORKSPACE
cd $WORKSPACE

if [ ! -d $REPO_PATH ]; then
  git hg clone "http://$HG_HOST/$HG_PATH" $REPO_PATH
  cd $REPO_PATH
  git remote add origin $SAPMACHINE_GIT_REPOSITORY
  git checkout -b "$HG_PATH"
else
  cd $REPO_PATH
  git remote remove origin
  git remote add origin $SAPMACHINE_GIT_REPOSITORY
  git checkout "$HG_PATH"
  git hg pull
fi

git push --tags origin "$HG_PATH"
