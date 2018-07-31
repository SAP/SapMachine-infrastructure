#!/bin/bash
set -ex

TIMESTAMP=`date +'%Y%m%d_%H_%M_%S'`
TIMESTAMP_LONG=`date +'%Y/%m/%d %H:%M:%S'`

export GITHUB_API_ACCESS_TOKEN=$SAPMACHINE_PUBLISH_GITHUB_TOKEN

PRE_RELEASE_OPT="-p"
if [ "$RELEASE" == true ]; then
  PRE_RELEASE_OPT=""
fi

if [ -z $GIT_TAG_NAME ]; then
    if [ ! -d SapMachine ]; then
        git clone -b $SAPMACHINE_GIT_BRANCH "http://$GIT_USER:$GIT_PASSWORD@$SAPMACHINE_GIT_REPO" SapMachine
    fi

    pushd SapMachine
    set +e
    SNAPSHOT_TAG=$(git tag -l --contains | grep snapshot)
    set -e
    if [ ! -z $SNAPSHOT_TAG ]; then
        echo "Snapshot already published"
        exit 0
    fi
    GIT_TAG_NAME="${SAPMACHINE_ARCHIVE_NAME_PREFIX}_snapshot-${TIMESTAMP}"
    git tag $GIT_TAG_NAME
    git push --tags
    popd
    GIT_TAG_DESCRIPTION="${SAPMACHINE_ARCHIVE_NAME_PREFIX} Snapshot ${TIMESTAMP_LONG}"
    python lib/github_publish.py -t $GIT_TAG_NAME -d "$GIT_TAG_DESCRIPTION" $PRE_RELEASE_OPT || true

else
    GIT_TAG_NAME=$(echo $GIT_TAG_NAME | sed 's/-alpine//')
    python lib/github_publish.py -t $GIT_TAG_NAME $PRE_RELEASE_OPT || true
fi

# replace the '+' by '.' - github replaces it anyway, but we want to have it consistent for sha256sum
#FILE_TAG_NAME=$(echo $GIT_TAG_NAME | sed 's/\+/\./')

FILE_NAME_JDK="$(ls sapmachine-jdk-*_bin.*)"
FILE_NAME_JRE="$(ls sapmachine-jre-*_bin.*)"

ARCHIVE_NAME_JDK="$(echo $FILE_NAME_JDK | sed 's/\+/\./')"
ARCHIVE_NAME_JRE="$(echo $FILE_NAME_JRE | sed 's/\+/\./')"

mv $FILE_NAME_JDK $ARCHIVE_NAME_JDK
mv $FILE_NAME_JRE $ARCHIVE_NAME_JRE

HAS_ZIP=$(ls sapmachine-jdk-*_bin.zip | wc -l)

if [ "$HAS_JRE" -lt "1" ]; then
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"
else
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/zip/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/zip/sha256\.txt/')"
fi

sha256sum $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE
sha256sum $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK

python lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JDK}"
python lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JRE}"
python lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JDK}"
python lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JRE}"
