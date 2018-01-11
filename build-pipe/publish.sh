#!/bin/bash
set -ex

TIMESTAMP=`date +'%Y%m%d_%H_%M_%S'`
TIMESTAMP_LONG=`date +'%Y/%m/%d %H:%M:%S'`

export GITHUB_TOKEN=$SAPMACHINE_PUBLISH_GITHUB_TOKEN
export GITHUB_USER=$SAPMACHINE_PUBLISH_GITHUB_USER
export GITHUB_REPO=$SAPMACHINE_PUBLISH_GITHUB_REPO_NAME

if [ -z $GIT_TAG_NAME ]; then
     git clone -b $SAPMACHINE_GIT_BRANCH "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine
    cd SapMachine
    SNAPSHOT_TAG=$(git tag --contains | grep snapshot)
    if [ ! -z $SNAPSHOT_TAG ]; then
        echo "Snapshot already published"
        exit 0
    fi
    git tag $GIT_TAG_NAME
    git push --tags
    GIT_TAG_NAME="${SAPMACHINE_ARCHIVE_NAME_PREFIX}_snapshot-${TIMESTAMP}"
    GIT_TAG_DESCRIPTION="${SAPMACHINE_ARCHIVE_NAME_PREFIX} Snapshot ${TIMESTAMP_LONG}"
    github-release release -t $GIT_TAG_NAME --pre-release -d "$GIT_TAG_DESCRIPTION"
else
    github-release release -t $GIT_TAG_NAME
fi

# replace the '+' by '.' - github replaces it anyway, but we want to have it consistent for sha256sum
FILE_TAG_NAME=$(echo $GIT_TAG_NAME | sed 's/\+/\./')

ARCHIVE_NAME_JDK="${SAPMACHINE_ARCHIVE_NAME_PREFIX}-${FILE_TAG_NAME}.tar.gz"
ARCHIVE_SUM_JDK="${SAPMACHINE_ARCHIVE_NAME_PREFIX}-${FILE_TAG_NAME}.sha256.txt"
ARCHIVE_FILE_JDK="${SAPMACHINE_ARCHIVE_NAME_PREFIX}-jdk.tar.gz"
ARCHIVE_NAME_JRE="${SAPMACHINE_ARCHIVE_NAME_PREFIX}-${FILE_TAG_NAME}-jre.tar.gz"
ARCHIVE_SUM_JRE="${SAPMACHINE_ARCHIVE_NAME_PREFIX}-${FILE_TAG_NAME}-jre.sha256.txt"
ARCHIVE_FILE_JRE="${SAPMACHINE_ARCHIVE_NAME_PREFIX}-jre.tar.gz"

mv $ARCHIVE_FILE_JRE $ARCHIVE_NAME_JRE
mv $ARCHIVE_FILE_JDK $ARCHIVE_NAME_JDK

sha256sum $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE
sha256sum $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK

github-release -v \
    upload \
    -t "${GIT_TAG_NAME}" \
    -n "${ARCHIVE_NAME_JDK}" \
    -f "${ARCHIVE_NAME_JDK}"

github-release -v \
    upload \
    -t "${GIT_TAG_NAME}" \
    -n "${ARCHIVE_NAME_JRE}" \
    -f "${ARCHIVE_NAME_JRE}"

github-release -v \
    upload \
    -t "${GIT_TAG_NAME}" \
    -n "${ARCHIVE_SUM_JRE}" \
    -f "${ARCHIVE_SUM_JRE}"

github-release -v \
    upload \
    -t "${GIT_TAG_NAME}" \
    -n "${ARCHIVE_SUM_JDK}" \
    -f "${ARCHIVE_SUM_JDK}"
