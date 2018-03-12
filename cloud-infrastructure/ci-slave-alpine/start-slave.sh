#!/bin/sh

while [ ! -f /var/slaves/${SLAVE_NAME}.txt ]
do
  echo "waiting for slave information '${SLAVE_NAME}'"
  sleep 5
done

secret=$(cat /var/slaves/${SLAVE_NAME}.txt)

java -jar /usr/share/jenkins/slave.jar -jnlpUrl ${MASTER_URL} -secret ${secret} -workDir ${AGENT_WORKDIR} ${SLAVE_NO_CERTIFICATE_CHECK}
