#!/bin/bash
set -ex

MSIFILE=$(ls *.msi)
python SapMachine-Infrastructure/lib/github_publish.py --tag=${GIT_TAG_NAME} --asset=${MSIFILE}
