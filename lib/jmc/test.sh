#!/bin/bash
set -ex

UNAME=`uname`
export PATH=$PATH:/usr/bin

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/jmc"

export PATH=${BUILD_JDK}:$PATH

./scripts/checkformatting.sh
./scripts/runcoretests.sh
./scripts/runapptests.sh
./scripts/runagenttests.sh
