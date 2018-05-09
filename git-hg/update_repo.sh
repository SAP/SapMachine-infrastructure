#!/bin/bash
set -ex

HG_HOST="hg.openjdk.java.net"
HG_PATH=$1


if [[ -z "$GIT_USER" ]] || [[ -z "$GIT_PASSWORD" ]]; then
    echo "Missing mandatory environment variables GIT_USER or GIT_PASSWORD"
    exit 1
fi

GIT_REPO="http://${GIT_USER}:${GIT_PASSWORD}@github.com/SAP/SapMachine"
REPO_PATH="$(basename $HG_PATH)"

echo $WORKSPACE
cd $WORKSPACE

if [ ! -d $REPO_PATH ]; then
  git hg clone "http://$HG_HOST/$HG_PATH" $REPO_PATH
  cd $REPO_PATH
  git remote add origin $GIT_REPO
  git checkout -b "$HG_PATH"
else
  cd $REPO_PATH
  git remote remove origin
  git remote add origin $GIT_REPO
  git checkout "$HG_PATH"
  git hg pull
fi

# we need the force push here, as jdk/jdk may contain jdk-10+xx tags,
# which leads to a conflict as the same tag is contained in the jdk/jdk10 repository
# as long we push the jdk10 branch after the jdk branch it's ok. However, we should fix this
# and delete  new jdk-10+xx tags in the jdk/jdk branch before pushing.

git push --tags --force origin "$HG_PATH"
