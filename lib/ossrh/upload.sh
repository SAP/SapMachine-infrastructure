#!/bin/bash
set -ex

MAJOR_VERSION=`echo $VERSION | cut -d . -f 1`

gpg --import $GPGSEC

mkdir upload
cd upload
cp ../SapMachine-Infrastructure/lib/ossrh/upload_pom.xml .
mvn -B --no-transfer-progress --settings $OSSRH_SETTINGS_XML -f upload_pom.xml -Dtype=jre -Dversion=$VERSION -DartefactSetVersion=$MAJOR_VERSION clean deploy
mvn -B --no-transfer-progress --settings $OSSRH_SETTINGS_XML -f upload_pom.xml -Dtype=jdk -Dversion=$VERSION -DartefactSetVersion=$MAJOR_VERSION | cut -d . -f 1` clean deploy

rm -rf ~/.gnupg/* $GPGSEC $OSSRH_SETTINGS_XML
