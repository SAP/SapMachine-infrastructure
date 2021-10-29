#!/bin/bash
set -ex

# Main
MAJOR=$(python3 ${WORKSPACE}/SapMachine-Infrastructure/lib/get_tag_major.py -t $GIT_TAG_NAME)

if [[ $MAJOR < 17 ]]; then
  DUPLEX=""
else
  DUPLEX="-d"
fi

python3 SapMachine-Infrastructure/lib/make_cask.py -t ${GIT_TAG_NAME} ${DUPLEX}
