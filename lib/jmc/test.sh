#!/bin/bash
set -ex

UNAME=`uname`

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

cd "${WORKSPACE}/jmc"

export PATH=${BUILD_JDK}:$PATH

if [[ $UNAME == CYGWIN* ]]; then
  cmd /c scripts\\runcoretests.bat
  cmd /c scripts\\startp2.bat
  cmd /c scripts\\runapptests.bat
  cmd /c scripts\\runagenttests.bat
  cmd /c scripts\\checkformatting.bat
else
  ./scripts/runcoretests.sh
  ./scripts/startp2.sh
  ./scripts/runapptests.sh
  ./scripts/runagenttests.sh
  ./scripts/checkformatting.sh
fi
