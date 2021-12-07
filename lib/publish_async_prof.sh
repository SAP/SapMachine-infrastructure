#!/bin/bash
set -ex

ARCHIVE_NAME="$(cat async-profiler/artifact.txt)"

python3 SapMachine-Infrastructure/lib/github_publish_asyncprof.py  -t $GIT_TAG_NAME -a "${ARCHIVE_NAME}"
