
FROM alpine:3.5

RUN apk update;     apk add wget ca-certificates zip git unzip coreutils python binutils shadow bash;

WORKDIR /etc/apk/keys
RUN wget https://sapmachine-ubuntu.sapcloud.io/alpine/sapmachine%40sap.com-5a673212.rsa.pub

WORKDIR /

RUN echo "http://sapmachine-ubuntu.sapcloud.io/alpine" >> /etc/apk/repositories

RUN apk update;     apk add sapmachine-10-jre=10.42.0-r0;

RUN groupadd -g 1001 jenkins; useradd -ms /bin/bash jenkins -u 1001 -g 1001

