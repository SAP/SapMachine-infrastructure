#!/bin/sh

MASTER_URL=$1
SECRET=$2
SLAVE_NO_CERTIFICATE_CHECK=$3

nohup java -jar /home/jenkins/slave.jar -jnlpUrl ${MASTER_URL} -secret ${SECRET} -workDir /home/jenkins/slave-home ${SLAVE_NO_CERTIFICATE_CHECK} &
