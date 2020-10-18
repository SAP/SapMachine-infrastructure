#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

if [[ $UNAME == CYGWIN* ]]; then
  WORKSPACE=$(cygpath -u "${WORKSPACE}")
fi

#GTEST_DIR="${WORKSPACE}/gtest"
#export GTEST_DIR

cd "${WORKSPACE}/SapMachine"

make run-test-gtest

cd "build"
cd "$(ls)"
cp test-results/gtest_all_server/gtest.xml "${WORKSPACE}"
