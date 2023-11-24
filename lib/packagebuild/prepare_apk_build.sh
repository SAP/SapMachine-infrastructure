#!/bin/bash

mkdir ~/.abuild
cp $apkrsa ~/.abuild/sapmachine-apk.rsa
chmod 600 ~/.abuild/sapmachine-apk.rsa
cp $apkrsapub ~/.abuild/sapmachine-apk.rsa.pub
chmod 644 ~/.abuild/sapmachine-apk.rsa.pub
sudo bash -c "cp $HOME/.abuild/sapmachine-apk.rsa.pub /etc/apk/keys/sapmachine-apk.rsa.pub"
echo -e PACKAGER_PRIVKEY="$HOME/.abuild/sapmachine-apk.rsa\n" > ~/.abuild/abuild.conf
ls -la ~/.abuild
cat ~/.abuild/abuild.conf
ls -la /etc/apk/keys
