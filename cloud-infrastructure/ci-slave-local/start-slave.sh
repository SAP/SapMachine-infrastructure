#!/bin/sh

MASTER_URL=$1
SECRET=$2
SLAVE_NO_CERTIFICATE_CHECK=$3

JAVA_ARGS="-Xms10g"

if [ -f nohup.out ]; then
    mv nohup.out "slave-$(date +"%d_%m_%y-%H_%M_%S_%N").out"
fi

nohup java -jar /home/jenkins/slave.jar -jnlpUrl ${MASTER_URL} -secret ${SECRET} -workDir /home/jenkins/slave-home ${SLAVE_NO_CERTIFICATE_CHECK} &
