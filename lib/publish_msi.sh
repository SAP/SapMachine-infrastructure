#!/bin/bash
set -ex

for MSIFILE in *.msi; do
    python SapMachine-Infrastructure/lib/github_publish.py --tag=${GIT_TAG_NAME} --asset=${MSIFILE}
done
