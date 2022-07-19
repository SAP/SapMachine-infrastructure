#!/bin/bash
set -ex

MAJOR_VERSION=$(echo $VERSION | cut -d . -f 1)
MINOR_VERSION=$(echo $VERSION | cut -d . -f 2)
INC_VERSION=$(echo $VERSION | cut -d . -f 3)

gpg --import $GPGSEC

mkdir upload
cd upload

mvn --version

cp ../SapMachine-Infrastructure/lib/ossrh/upload_pom.xml .
sed -i "s/\${type}/jre/g" upload_pom.xml
sed -i "s/\${version}/$VERSION/g" upload_pom.xml
sed -i "s/\${maven.name}/SapMachine JRE/g" upload_pom.xml
if [[ $MAJOR_VERSION == 11 && $MINOR_VERSION == 0 && $INC_VERSION -lt 16 ]]; then
    sed -i "s/\${macosx.platform.name}/osx/g" upload_pom.xml
    sed -i "s/\${skip.macaarch}/true/g" upload_pom.xml
else
    sed -i "s/\${macosx.platform.name}/macos/g" upload_pom.xml
    sed -i "s/\${skip.macaarch}/false/g" upload_pom.xml
fi
mvn -B --no-transfer-progress --settings $OSSRH_SETTINGS_XML -f upload_pom.xml clean deploy

cp -f ../SapMachine-Infrastructure/lib/ossrh/upload_pom.xml .
sed -i "s/\${type}/jdk/g" upload_pom.xml
sed -i "s/\${version}/$VERSION/g" upload_pom.xml
sed -i "s/\${maven.name}/SapMachine JDK/g" upload_pom.xml
if [[ $MAJOR_VERSION == 11 && $MINOR_VERSION == 0 && $INC_VERSION -lt 16 ]]; then
    sed -i "s/\${macosx.platform.name}/osx/g" upload_pom.xml
    sed -i "s/\${skip.macaarch}/true/g" upload_pom.xml
else
    sed -i "s/\${macosx.platform.name}/macos/g" upload_pom.xml
    sed -i "s/\${skip.macaarch}/false/g" upload_pom.xml
fi
mvn -B --no-transfer-progress --settings $OSSRH_SETTINGS_XML -f upload_pom.xml clean deploy

rm -rf ~/.gnupg/* $GPGSEC $OSSRH_SETTINGS_XML
