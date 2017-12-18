#!/bin/bash
set -ex

MAJOR_VERSION=$1

PR_BASE="sapmachine"
if [ $MAJOR_VERSION == 10 ]; then
  PR_BASE="sapmachine10"
fi

if [ -d SapMachine ]; then
    rm -rf SapMachine;
fi
export GIT_COMMITTER_NAME=$GIT_USER
export GIT_COMMITTER_EMAIL="sapmachine@sap.com"
git clone -b $PR_BASE "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine

pushd SapMachine
git config user.email $GIT_COMMITTER_EMAIL
git config user.name $GIT_USER

REGEXP="s/jdk\-$MAJOR_VERSION\+([0-9]*)/\1/p"
LAST_BUILD_JDK_TAG=$(git tag | sed -rn $REGEXP | sort -nr | head -n1)

GIT_TAG="jdk-$MAJOR_VERSION+$LAST_BUILD_JDK_TAG"
echo "LAST_JDK_TAG=$GIT_TAG"
set +e
CONTAINING_BRANCHES=$(git branch -a --contains tags/jdk-$MAJOR_VERSION+$LAST_BUILD_JDK_TAG | grep -E "(sapmachine|merge-$GIT_TAG )")
set -e
if [ -z "$CONTAINING_BRANCHES" ]; then
  echo "Merging tag ${GIT_TAG}"
  git checkout -b "merge-$GIT_TAG"
  git merge ${GIT_TAG}^0
  git push origin "merge-$GIT_TAG"
  popd
else
  echo "Already merged, nothing to do."
  popd
  exit 0
fi

PR_DATA="{\"title\":\"Merge to tag $GIT_TAG\",\"body\":\"please pull\",\"head\":\"merge-$GIT_TAG\",\"base\":\"$PR_BASE\"}"

curl -H "Content-Type: application/json" \
 --data "$PR_DATA" "https://$GIT_USER:$SAPMACHINE_PUBLISH_GITHUB_TOKEN@api.github.com/repos/SAP/SapMachine/pulls"
