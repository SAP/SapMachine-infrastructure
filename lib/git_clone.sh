#!/bin/bash
set -e

if [[ `uname` == CYGWIN* ]]; then
  GIT_TOOL=/cygdrive/c/Program\ Files/Git/cmd/git.exe
else
  GIT_TOOL=git
fi

"$GIT_TOOL" --version
set -ex
"$GIT_TOOL" init $2 && cd $2
GIT_TERMINAL_PROMPT=0 "$GIT_TOOL" fetch --depth 1 $1 $3
"$GIT_TOOL" checkout --detach FETCH_HEAD
