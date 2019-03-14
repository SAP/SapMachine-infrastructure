#!/bin/bash
set -ex

TIMESTAMP=`date +'%Y%m%d_%H_%M_%S'`
TIMESTAMP_LONG=`date +'%Y/%m/%d %H:%M:%S'`

export GITHUB_API_ACCESS_TOKEN=$SAPMACHINE_PUBLISH_GITHUB_TOKEN

PRE_RELEASE_OPT="-p"
if [ "$RELEASE" == true ]; then
  PRE_RELEASE_OPT=""
fi

if [[ -z $SAPMACHINE_GIT_REPOSITORY ]]; then
  SAPMACHINE_GIT_REPOSITORY="http://github.com/SAP/SapMachine.git"
fi

if [ -z $GIT_TAG_NAME ]; then
    if [ ! -d SapMachine ]; then
        git clone -b $SAPMACHINE_GIT_BRANCH $SAPMACHINE_GIT_REPOSITORY SapMachine
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
    python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -d "$GIT_TAG_DESCRIPTION" $PRE_RELEASE_OPT || true

else
    GIT_TAG_NAME=$(echo $GIT_TAG_NAME | sed 's/-alpine//')
    python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME $PRE_RELEASE_OPT || true
fi

ls -la

FILE_NAME_JDK="$(cat jdk_bundle_name.txt)"
FILE_NAME_JRE="$(cat jre_bundle_name.txt)"


if [ "$RELEASE" == true ]; then
  # remove build number +xx from release build filenames
  ARCHIVE_NAME_JDK="$(echo $FILE_NAME_JDK | sed 's/\+[0-9]*//')"
  ARCHIVE_NAME_JRE="$(echo $FILE_NAME_JRE | sed 's/\+[0-9]*//')"
else
  # substitute build number +xx to .xx to avoid problmes with uploads. + is no good character :-)
  ARCHIVE_NAME_JDK="$(echo $FILE_NAME_JDK | sed 's/\+/\./')"
  ARCHIVE_NAME_JRE="$(echo $FILE_NAME_JRE | sed 's/\+/\./')"
fi
mv $FILE_NAME_JDK $ARCHIVE_NAME_JDK
mv $FILE_NAME_JRE $ARCHIVE_NAME_JRE

HAS_ZIP=$(ls sapmachine-jdk-*_bin.zip | wc -l)

if [ "$HAS_ZIP" -lt "1" ]; then
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"
else
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/zip/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/zip/sha256\.txt/')"
fi

shasum -a 256 $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK
shasum -a 256 $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE

python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JDK}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JRE}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JDK}"
python SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JRE}"
