#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

if [[ $UNAME == CYGWIN* ]]; then
  WORKSPACE=$(cygpath -u "${WORKSPACE}")
fi

if [ -d gtest ]; then
  rm -rf gtest;
fi

GTEST_DIR="${WORKSPACE}/gtest"
export GTEST_DIR
git clone -b release-1.8.1 https://github.com/google/googletest.git $GTEST_DIR

cd "${WORKSPACE}/SapMachine"

GTEST_RESULT_PATH="gtest_all_server"

make run-test-gtest

cp ../test-results/$GTEST_RESULT_PATH/gtest.xml "${WORKSPACE}"
