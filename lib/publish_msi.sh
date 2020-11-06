#!/bin/bash
set -ex

for MSIFILE in *.msi; do
    python3 SapMachine-Infrastructure/lib/github_publish.py -t ${GIT_TAG_NAME} -a ${MSIFILE}
done
