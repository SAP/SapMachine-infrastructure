#!/bin/bash

if [ -d SapMachine ]; then
    rm -rf SapMachine;
fi
export GIT_COMMITTER_NAME=$GIT_USER
export GIT_COMMITTER_EMAIL="sapmachine@sap.com"
git clone -b "jdk/jdk" "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine

cd SapMachine

LAST_BUILD_TAG=$(git tag | sed -rn 's/jdk\-10\+([0-9]*)/\1/p' | sort -nr | head -n1)

echo "LAST_BUILD_TAG=$LAST_BUILD_TAG"

# check if we have already a Build

HTTP_CODE=$(curl -I -s -w "%{http_code}" -o /dev/null \
https://githuom/SAP/SapMachine/releases/download/jdk-10%2B${LAST_BUILD_TAG}/sapmachine_linux-x64-jdk-10.${LAST_BUILD_TAG}.tar.gz)

if [ $HTTP_CODE == 302 ]; then
  echo "nothing to do."
  exit 0
fi

#trigger a Build
CRUMB=$(wget -q --auth-no-challenge --user $JENKINS_USER --password $JENKINS_PASSWORD \
--output-document - 'http://sapmachine-ci.sapcloud.io/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)')

curl -X POST https://$JENKINS_USER:$JENKINS_TOKEN@sapmachine-ci.sapcloud.io/job/build-pipeline/buildWithParameters \
-H "$CRUMB" --data-urlencode token=test-token --data-urlencode "GIT_TAG_NAME=jdk-10+$LAST_BUILD_TAG"
