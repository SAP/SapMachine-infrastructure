#!/bin/bash
set -ex

RPMFILE=$(ls *.rpm)
python3 SapMachine-infrastructure/lib/github_publish.py -t ${GIT_TAG_NAME} -a ${RPMFILE}
