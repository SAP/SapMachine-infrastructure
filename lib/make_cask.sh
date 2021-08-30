#!/bin/bash
set -ex

echo 'will check for casks here...'

TIMESTAMP=`date +'%Y%m%d_%H_%M_%S'`
TIMESTAMP_LONG=`date +'%Y/%m/%d %H:%M:%S'`

export GITHUB_API_ACCESS_TOKEN=$SAPMACHINE_PUBLISH_GITHUB_TOKEN

echo 'will check for casks here...'
echo "GITHUB_API_ACCESS_TOKEN: $GITHUB_API_ACCESS_TOKEN"
echo "SAPMACHINE_GIT_REPOSITORY: $SAPMACHINE_GIT_REPOSITORY"

ls -la
