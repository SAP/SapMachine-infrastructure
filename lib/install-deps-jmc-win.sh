#!/bin/bash
set -ex

UNAME=`uname`
export PATH=$PATH:/usr/bin

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

if [[ ! -z $GIT_TAG_NAME ]]; then
  VERSION=${GIT_TAG_NAME:1:3}
else
  VERSION=snapshot
fi


cd "${WORKSPACE}"

wget https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.14.1/sapmachine-jdk-11.0.14.1_windows-x64_bin.zip
unzip sapmachine-jdk-11.0.14.1_windows-x64_bin.zip
export JAVA_HOME="`pwd`/sapmachine-jdk-11.0.14.1"
export PATH="`pwd`/sapmachine-jdk-11.0.14.1/bin:$PATH"
wget https://dlcdn.apache.org/maven/maven-3/3.8.4/binaries/apache-maven-3.8.4-bin.zip
unzip apache-maven-3.8.4-bin.zip
export PATH="`pwd`/apache-maven-3.8.4/bin:$PATH"