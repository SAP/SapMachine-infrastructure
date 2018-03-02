
FROM alpine:3.5

RUN apk update;     apk add wget ca-certificates;

WORKDIR /etc/apk/keys
RUN wget https://dist.sapmachine.io/alpine/sapmachine%40sap.com-5a673212.rsa.pub

WORKDIR /

RUN echo "http://dist.sapmachine.io/alpine/3.5" >> /etc/apk/repositories

RUN apk update;     apk add sapmachine-11-jre=11.3.0-r0;



