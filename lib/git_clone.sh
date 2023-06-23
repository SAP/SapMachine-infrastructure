#!/bin/bash
set -e

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

echo "Git User: ${GIT_USER}"
echo "Git Password (length): ${#GIT_PASSWORD}"
echo "Credential stuff: ${GIT_CREDENTIALS}"

"$GIT_TOOL" --version
"$GIT_TOOL" config --global init.defaultBranch master
(set -ex && "$GIT_TOOL" init $2)
cd $2

# handle tag
if GIT_TERMINAL_PROMPT=0 "$GIT_TOOL" ls-remote --tags "$1" | grep -q "refs/tags/$3$"; then
  if [ ! -z $4 ]; then
    echo "Should not happen: Try to merge $4 into tag($3)"
    exit -1
  fi
  (set -ex && GIT_TERMINAL_PROMPT=0 eval "$GIT_TOOL_FOR_EVAL" $GIT_CREDENTIALS fetch --depth 1 $1 $3)
  (set -ex && "$GIT_TOOL" checkout --detach FETCH_HEAD)
# handle branch
elif GIT_TERMINAL_PROMPT=0 "$GIT_TOOL" ls-remote --heads "$1" | grep -q "refs/heads/$3"; then
  if [ ! -z $4 ]; then
    (set -ex && GIT_TERMINAL_PROMPT=0 eval "$GIT_TOOL_FOR_EVAL" $GIT_CREDENTIALS fetch --no-tags $1 $3:ref pull/$4/head:pr)
    (set -ex && "$GIT_TOOL" checkout ref)
    git config user.name SAPMACHINE_PR_TEST
    git config user.email sapmachine@sap.com
    (set -ex && "$GIT_TOOL" merge pr)
  else
    (set -ex && GIT_TERMINAL_PROMPT=0 eval "$GIT_TOOL_FOR_EVAL" $GIT_CREDENTIALS fetch --no-tags --depth 1 $1 $3)
    (set -ex && "$GIT_TOOL" checkout --detach FETCH_HEAD)
  fi
else
  echo "$3 is not a valid git reference"
  exit -1
fi
