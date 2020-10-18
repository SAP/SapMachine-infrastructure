#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

if [[ $UNAME == CYGWIN* ]]; then
  WORKSPACE=$(cygpath -u "${WORKSPACE}")
fi

exit -1
return -1

cd "${WORKSPACE}/SapMachine"

make run-test-gtest

cd "build"
cd "$(ls)"
cp test-results/gtest_all_server/gtest.xml "${WORKSPACE}"
