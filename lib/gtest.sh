#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

if [[ $UNAME == CYGWIN* ]]; then
  WORKSPACE=$(cygpath -u "${WORKSPACE}")
fi

GTEST_DIR="${WORKSPACE}/gtest"
export GTEST_DIR

GTEST_RESULT_PATH="gtest_all_server"

cd "${WORKSPACE}/SapMachine"

make run-test-gtest

cp test-results/$GTEST_RESULT_PATH/gtest.xml "${WORKSPACE}"
