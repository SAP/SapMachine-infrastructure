#!/bin/bash
set -ex

git init SapMachine && cd SapMachine
git remote add origin $SAPMACHINE_GIT_REPOSITORY
git fetch origin $GIT_REF
git checkout FETCH_HEAD
