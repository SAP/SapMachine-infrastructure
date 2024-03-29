#!/bin/bash
set -ex

MAJOR_VERSION=$(echo $VERSION | cut -d . -f 1)

gpg --import $GPGSEC

mkdir upload
cd upload

mvn --version

cp ../SapMachine-infrastructure/lib/ossrh/upload_pom.xml .
sed -i "s/\${type}/jre/g" upload_pom.xml
sed -i "s/\${version}/$VERSION/g" upload_pom.xml
sed -i "s/\${maven.name}/SapMachine JRE/g" upload_pom.xml
if [[ $MAJOR_VERSION == 11 ]]; then
    sed -i "s/\${skip.musl}/true/g" upload_pom.xml
else
    sed -i "s/\${skip.musl}/false/g" upload_pom.xml
fi
if [[ $MAJOR_VERSION -lt 21 ]]; then
    sed -i "s/\${skip.aix}/true/g" upload_pom.xml
else
    sed -i "s/\${skip.aix}/false/g" upload_pom.xml
fi
mvn -B --no-transfer-progress --settings $OSSRH_SETTINGS_XML -f upload_pom.xml clean deploy

cp -f ../SapMachine-infrastructure/lib/ossrh/upload_pom.xml .
sed -i "s/\${type}/jdk/g" upload_pom.xml
sed -i "s/\${version}/$VERSION/g" upload_pom.xml
sed -i "s/\${maven.name}/SapMachine JDK/g" upload_pom.xml
if [[ $MAJOR_VERSION == 11 ]]; then
    sed -i "s/\${skip.musl}/true/g" upload_pom.xml
else
    sed -i "s/\${skip.musl}/false/g" upload_pom.xml
fi
if [[ $MAJOR_VERSION -lt 21 ]]; then
    sed -i "s/\${skip.aix}/true/g" upload_pom.xml
else
    sed -i "s/\${skip.aix}/false/g" upload_pom.xml
fi
mvn -B --no-transfer-progress --settings $OSSRH_SETTINGS_XML -f upload_pom.xml clean deploy

rm -rf ~/.gnupg/* $GPGSEC $OSSRH_SETTINGS_XML
