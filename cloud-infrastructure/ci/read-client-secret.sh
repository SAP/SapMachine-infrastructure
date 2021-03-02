#!/bin/sh

CLIENT_NAME=$1

while [ ! -f /var/clients/${CLIENT_NAME}.txt ]
do
  sleep 2
done

secret=$(cat /var/clients/${CLIENT_NAME}.txt)$

echo $secret

