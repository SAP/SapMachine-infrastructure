#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/async-profiler"

export JAVA_HOME=${BUILD_JDK}

make test
