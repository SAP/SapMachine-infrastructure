#!/bin/bash
set -ex

TIMESTAMP=`date +'%Y%m%d_%H_%M_%S'`
TIMESTAMP_LONG=`date +'%Y/%m/%d %H:%M:%S'`
UNAME=`uname`

export GITHUB_API_ACCESS_TOKEN=$SAPMACHINE_PUBLISH_GITHUB_TOKEN

PRE_RELEASE_OPT="-p"
if [ "$RELEASE" == true ]; then
  PRE_RELEASE_OPT=""

  if [[ $UNAME == Darwin ]]; then
    exit 0
  fi
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
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -d "$GIT_TAG_DESCRIPTION" $PRE_RELEASE_OPT | true
else
    GIT_TAG_NAME=$(echo $GIT_TAG_NAME | sed 's/-alpine//')
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME $PRE_RELEASE_OPT | true
fi

ls -la

ARCHIVE_NAME_JDK="$(cat jdk_bundle_name.txt)"
ARCHIVE_NAME_JRE="$(cat jre_bundle_name.txt)"
ARCHIVE_NAME_SYMBOLS="$(cat symbols_bundle_name.txt)"

HAS_ZIP=$(ls sapmachine-jdk-*_bin.zip | wc -l)

if [ "$HAS_ZIP" -lt "1" ]; then
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/tar\.gz/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/tar\.gz/sha256\.txt/')"
else
    ARCHIVE_SUM_JDK="$(echo $ARCHIVE_NAME_JDK | sed 's/zip/sha256\.txt/')"
    ARCHIVE_SUM_JRE="$(echo $ARCHIVE_NAME_JRE | sed 's/zip/sha256\.txt/')"
fi
ARCHIVE_SUM_SYMBOLS="$(echo $ARCHIVE_NAME_SYMBOLS | sed 's/tar\.gz/sha256\.txt/')"

shasum -a 256 $ARCHIVE_NAME_JDK > $ARCHIVE_SUM_JDK
shasum -a 256 $ARCHIVE_NAME_JRE > $ARCHIVE_SUM_JRE
shasum -a 256 $ARCHIVE_NAME_SYMBOLS > $ARCHIVE_SUM_SYMBOLS

python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_NAME_SYMBOLS}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JDK}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_JRE}"
python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${ARCHIVE_SUM_SYMBOLS}"

if [[ $UNAME == Darwin ]]; then
    DMG_NAME_JDK="$(cat jdk_dmg_name.txt)"
    DMG_NAME_JRE="$(cat jre_dmg_name.txt)"

    DMG_SUM_JDK="$(echo $DMG_NAME_JDK | sed 's/dmg/sha256\.dmg\.txt/')"
    DMG_SUM_JRE="$(echo $DMG_NAME_JRE | sed 's/dmg/sha256\.dmg\.txt/')"

    shasum -a 256 $DMG_NAME_JDK > $DMG_SUM_JDK
    shasum -a 256 $DMG_NAME_JRE > $DMG_SUM_JRE

    python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_NAME_JDK}"
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_NAME_JRE}"
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_SUM_JDK}"
    python3 SapMachine-Infrastructure/lib/github_publish.py -t $GIT_TAG_NAME -a "${DMG_SUM_JRE}"

    JDK_SHA256=`shasum -a 256 $DMG_NAME_JDK | awk '{ print $1 }'`
    JRE_SHA256=`shasum -a 256 $DMG_NAME_JRE | awk '{ print $1 }'`

    python3 SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $JDK_SHA256 -i jdk $PRE_RELEASE_OPT
    python3 SapMachine-Infrastructure/lib/make_cask.py -t $GIT_TAG_NAME --sha256sum $JRE_SHA256 -i jre $PRE_RELEASE_OPT
fi
