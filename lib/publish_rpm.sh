#!/bin/bash
set -ex

RPMFILE=$(ls *.rpm)
python3 SapMachine-Infrastructure/lib/github_publish.py --tag=${GIT_TAG_NAME} --asset=${RPMFILE}
