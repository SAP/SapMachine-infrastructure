
FROM alpine:3.5

RUN apk update;     apk add wget ca-certificates zip git unzip coreutils python binutils shadow bash;

WORKDIR /etc/apk/keys
RUN wget https://dist.sapmachine.io/alpine/sapmachine%40sap.com-5a673212.rsa.pub

WORKDIR /

RUN echo "http://dist.sapmachine.io/alpine/3.5" >> /etc/apk/repositories

RUN apk update;     apk add sapmachine-11-jre=11.10.0-r0;

RUN groupadd -g 1002 jenkins; useradd -ms /bin/bash jenkins -u 1002 -g 1002

