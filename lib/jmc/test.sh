#!/bin/bash
set -ex

UNAME=`uname`

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/jmc"

export PATH=${BUILD_JDK}:$PATH

if [[ $UNAME == CYGWIN* ]]; then
  cmd /c scripts\\checkformatting.bat
  cmd /c scripts\\runcoretests.bat
  cmd /c scripts\\runapptests.bat
  cmd /c scripts\\runagenttests.bat
else
  ./scripts/checkformatting.sh
  ./scripts/runcoretests.sh
  ./scripts/runapptests.sh
  ./scripts/runagenttests.sh
fi
