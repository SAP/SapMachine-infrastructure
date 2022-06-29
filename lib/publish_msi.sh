#!/bin/bash
set -ex

if [[ -z "$SAPMACHINE_VERSION" ]]; then
    echo "SAPMACHINE_VERSION not set"
    exit 1
fi

for MSIFILE in *.msi; do
    shasum -a 256 $MSIFILE > ${MSIFILE}.sha256.txt
    python3 SapMachine-Infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${MSIFILE}
    python3 SapMachine-Infrastructure/lib/github_publish.py -t ${SAPMACHINE_VERSION} -a ${MSIFILE}.sha256.txt
done
