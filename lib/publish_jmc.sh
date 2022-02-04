#!/bin/bash
set -ex

ARCHIVE_NAME="$(cat jmc/artifact.txt)"

python3 SapMachine-Infrastructure/lib/github_publish_jmc.py  -t $GIT_TAG_NAME -a "${ARCHIVE_NAME}"
