
FROM alpine:3.5

RUN apk update;     apk add wget ca-certificates zip git unzip coreutils python binutils;

WORKDIR /etc/apk/keys
RUN wget https://sapmachine-ubuntu.sapcloud.io/alpine/sapmachine%40sap.com-5a673212.rsa.pub

WORKDIR /

RUN echo "http://sapmachine-ubuntu.sapcloud.io/alpine" >> /etc/apk/repositories

RUN apk update;     apk add sapmachine-10-jre=10.41.0-r0;



