#!/bin/sh

jenkins_key_exists=$(gpg --list-keys | grep jenkins | wc -l)

if [ "$jenkins_key_exists" = "0" ]; then
  gpg --import-ownertrust /var/pkg/deb/keys/sapmachine.ownertrust
  gpg --import /var/pkg/deb/keys/sapmachine.secret.key
fi

while [ ! -f /var/clients/${CLIENT_NAME}.txt ]
do
  echo "waiting for client information '${CLIENT_NAME}'"
  sleep 5
done

secret=$(cat /var/clients/${CLIENT_NAME}.txt)

java -jar /usr/share/jenkins/client.jar -jnlpUrl ${SERVER_URL} -secret ${secret} -workDir ${AGENT_WORKDIR} ${CLIENT_NO_CERTIFICATE_CHECK}
