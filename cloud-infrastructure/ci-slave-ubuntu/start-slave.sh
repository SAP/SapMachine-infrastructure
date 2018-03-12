#!/bin/sh

jenkins_key_exists=$(gpg --list-keys | grep jenkins | wc -l)

if [ "$jenkins_key_exists" = "0" ]; then
  gpg --import-ownertrust /var/pkg/deb/keys/sapmachine.ownertrust
  gpg --import /var/pkg/deb/keys/sapmachine.secret.key
fi

while [ ! -f /var/slaves/${SLAVE_NAME}.txt ]
do
  echo "waiting for slave information '${SLAVE_NAME}'"
  sleep 5
done

secret=$(cat /var/slaves/${SLAVE_NAME}.txt)

java -jar /usr/share/jenkins/slave.jar -jnlpUrl ${MASTER_URL} -secret ${secret} -workDir ${AGENT_WORKDIR} ${SLAVE_NO_CERTIFICATE_CHECK}
