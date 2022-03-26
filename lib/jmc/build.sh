#!/bin/bash
set -ex

UNAME=`uname`

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/jmc"

export PATH=${BUILD_JDK}:$PATH

rm -rf target

if [[ $UNAME == CYGWIN* ]]; then
  cmd /c build.bat --packageJmc
else
  ./build.sh --packageJmc
fi
