#!/bin/bash
set -e

DEPTH_OPTION="--depth 1"
if [ ! -z $4 ]; then
  if [[ $4 == deep ]]; then
    DEPTH_OPTION=
  fi
fi

if [[ `uname` == CYGWIN* ]]; then
  GIT_TOOL="/cygdrive/c/Program Files/Git/cmd/git.exe"
  GIT_TOOL_FOR_EVAL="/cygdrive/c/Program\ Files/Git/cmd/git.exe"
else
  GIT_TOOL=git
  GIT_TOOL_FOR_EVAL=git
fi

if [ ! -z $GIT_USER ]; then
  GIT_CREDENTIALS="-c credential.helper='!f() { sleep 1; echo \"username=${GIT_USER}\"; echo \"password=${GIT_PASSWORD}\"; }; f'"
fi

"$GIT_TOOL" --version
set -ex
"$GIT_TOOL" init $2 && cd $2
GIT_TERMINAL_PROMPT=0 eval "$GIT_TOOL_FOR_EVAL" $GIT_CREDENTIALS fetch $DEPTH_OPTION $1 $3
"$GIT_TOOL" checkout --detach FETCH_HEAD
