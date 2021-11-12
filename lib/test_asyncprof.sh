#!/bin/bash
set -ex

UNAME=`uname`

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/async-profiler"

export JAVA_HOME=${BUILD_JDK}

test/smoke-test.sh
test/thread-smoke-test.sh
test/alloc-smoke-test.sh
test/load-library-test.sh
