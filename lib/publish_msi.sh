#!/bin/bash
set -ex

if [ "$SAPMACHINE_VERSION" != "" ]; then
    VERSION_TAG=$SAPMACHINE_VERSION
elif [ "$GIT_REF" != "" ]; then
    VERSION_TAG=$GIT_REF
else
    echo "Neither SAPMACHINE_VERSION nor GIT_REF were set"
    exit 1
fi

for MSIFILE in *.msi; do
    python3 SapMachine-Infrastructure/lib/github_publish.py -t ${VERSION_TAG} -a ${MSIFILE}
done
