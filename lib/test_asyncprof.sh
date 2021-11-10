#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/async-profiler"

export JAVA_HOME=${BUILD_JDK}

sudo sysctl kernel.perf_event_paranoid=1

make test
