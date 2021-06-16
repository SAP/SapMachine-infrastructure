#!/bin/bash
set -ex

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

if [[ $UNAME == CYGWIN* ]]; then
  WORKSPACE=$(cygpath -u "${WORKSPACE}")
fi

cd "${WORKSPACE}/SapMachine"

make test TEST="gtest"

cd "build"
cd "$(ls)"
cp test-results/gtest_all_server/gtest.xml "${WORKSPACE}"
