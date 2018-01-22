#!/bin/bash
set -ex

TIMESTAMP=`date +'%Y%m%d_%H_%M_%S'`
TIMESTAMP_LONG=`date +'%Y/%m/%d %H:%M:%S'`

export GITHUB_TOKEN=$SAPMACHINE_PUBLISH_GITHUB_TOKEN
export GITHUB_USER=$SAPMACHINE_PUBLISH_GITHUB_USER
export GITHUB_REPO=$SAPMACHINE_PUBLISH_GITHUB_REPO_NAME

if [ -z $GIT_TAG_NAME ]; then
    if [ ! -d SapMachine ]; then
        git clone -b $SAPMACHINE_GIT_BRANCH "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine
    fi

    pushd SapMachine
    set +e
    SNAPSHOT_TAG=$(git tag --contains | grep snapshot)
    set -e
    if [ ! -z $SNAPSHOT_TAG ]; then
        echo "Snapshot already published"
        exit 0
    fi
    git tag $GIT_TAG_NAME
    git push --tags
    cd ..
    GIT_TAG_NAME="${SAPMACHINE_ARCHIVE_NAME_PREFIX}_snapshot-${TIMESTAMP}"
    GIT_TAG_DESCRIPTION="${SAPMACHINE_ARCHIVE_NAME_PREFIX} Snapshot ${TIMESTAMP_LONG}"
    github-release release -t $GIT_TAG_NAME --pre-release -d "$GIT_TAG_DESCRIPTION"

else
    GIT_TAG_NAME=$(echo $GIT_TAG_NAME | sed 's/-alpine//')
    github-release release -t $GIT_TAG_NAME
fi

# replace the '+' by '.' - github replaces it anyway, but we want to have it consistent for sha256sum
#FILE_TAG_NAME=$(echo $GIT_TAG_NAME | sed 's/\+/\./')

FILE_NAME_JDK="$(ls sapmachine-jdk-*_bin.tar.gz)"
FILE_NAME_JRE="$(ls sapmachine-jre-*_bin.tar.gz)"

ARCHIVE_NAME_JDK="$(echo $FILE_NAME_JDK | sed 's/\+/\./')"
ARCHIVE_NAME_JRE="$(echo $FILE_NAME_JRE | sed 's/\+/\./')"

mv $FILE_NAME_JDK $ARCHIVE_NAME_JDK
mv $FILE_NAME_JRE $ARCHIVE_NAME_JRE

ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"

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
