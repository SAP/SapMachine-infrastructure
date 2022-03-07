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

test -e zulu11.54.25-ca-jdk11.0.14.1-macosx_aarch64.tar.gz || wget https://cdn.azul.com/zulu/bin/zulu11.54.25-ca-jdk11.0.14.1-macosx_aarch64.tar.gz
rm -fr zulu11.54.25-ca-jdk11.0.14.1-macosx_aarch64 boot_jdk
tar xf zulu11.54.25-ca-jdk11.0.14.1-macosx_aarch64.tar.gz
mv zulu11.54.25-ca-jdk11.0.14.1-macosx_aarch64 boot_jdk
export JAVA_HOME="`pwd`/boot_jdk"
export PATH="`pwd`/boot_jdk/bin:$PATH"
test -e apache-maven-3.8.4-bin.zip || wget https://dlcdn.apache.org/maven/maven-3/3.8.4/binaries/apache-maven-3.8.4-bin.zip
rm -fr apache-maven-3.8.4
unzip apache-maven-3.8.4-bin.zip
export PATH="`pwd`/apache-maven-3.8.4/bin:$PATH"