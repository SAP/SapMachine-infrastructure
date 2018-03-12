#!/bin/sh

SLAVE_NAME=$1

while [ ! -f /var/slaves/${SLAVE_NAME}.txt ]
do
  sleep 2
done

secret=$(cat /var/slaves/${SLAVE_NAME}.txt)$

echo $secret

