#!/bin/sh

PW_FILE=/var/jenkins_home/secrets/sapmachinePassword

while [ ! -f $PW_FILE ]
do
  sleep 2
done

cat $PW_FILE

