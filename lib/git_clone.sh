#!/bin/bash
set -e

DEPTH_OPTION="--depth 1"
PR_REF=
PR_SPEC=
if [ ! -z $4 ]; then
  DEPTH_OPTION=
  PR_REF=pull/$4/head
  PR_SPEC=$PR_REF:pr
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
(set -ex && "$GIT_TOOL" init $2)
cd $2
(set -ex && GIT_TERMINAL_PROMPT=0 eval "$GIT_TOOL_FOR_EVAL" $GIT_CREDENTIALS fetch --no-tags $DEPTH_OPTION $1 $3:ref $PR_SPEC)
(set -ex && "$GIT_TOOL" checkout ref)
if [ ! -z $4 ]; then
  git config user.name SAPMACHINE_PR_TEST
  git config user.email sapmachine@sap.com
  (set -ex && git merge pr)
fi
