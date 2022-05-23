#!/bin/bash
set -ex

mkdir SapMachine
cd SapMachine
git init
git remote add origin $SAPMACHINE_GIT_REPOSITORY
git fetch origin $GIT_REF
git checkout FETCH_HEAD
