#!/bin/bash
set -ex

if [ -d SapMachine ]; then
    rm -rf SapMachine;
fi
export GIT_COMMITTER_NAME=$GIT_USER
export GIT_COMMITTER_EMAIL="sapmachine@sap.com"
git clone -b "sapmachine-test-merge" "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine

cd SapMachine

LAST_BUILD_JDK_TAG=$(git tag | sed -rn 's/jdk\-10\+([0-9]*)/\1/p' | sort -nr | head -n1)

GIT_TAG="jdk-10+$LAST_BUILD_JDK_TAG"
echo "LAST_JDK_TAG=$GIT_TAG"

#if [ -z "$(git branch -a --contains tags/jdk-10+$LAST_BUILD_JDK_TAG | grep sapmachine )" ]; then
if [ -z "$(git branch -a --contains tags/jdk-10+$LAST_BUILD_JDK_TAG | grep sapmachine-test-merge )" ]; then
  echo "Merging tag ${GIT_TAG}"
  git checkout -b "merge-$GIT_TAG"
  git merge ${GIT_TAG}^0
  git push origin "merge-$GIT_TAG"
else
  echo "Already merged, nothing to do."
fi
