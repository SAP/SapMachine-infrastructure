#!/bin/bash
set -ex

RPMFILE=$(ls *.rpm)
python SapMachine-Infrastructure/lib/github_publish.py --tag=${GIT_TAG_NAME} --asset=${RPMFILE}
