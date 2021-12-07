#!/bin/bash
set -ex

cd "${WORKSPACE}/async-profiler"

ARCHIVE_NAME="$(cat artifact.txt)"

python3 SapMachine-Infrastructure/lib/github_publish_asyncprof.py  -t $GIT_TAG_NAME -a "${ARCHIVE_NAME}"
