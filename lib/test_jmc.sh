#!/bin/bash
set -ex

UNAME=`uname`

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/jmc"

export JAVA_HOME=${BUILD_JDK}

./scripts/checkformatting.sh
./scripts/runcoretests.sh
./scripts/runapptests.sh
./scripts/runagenttests.sh