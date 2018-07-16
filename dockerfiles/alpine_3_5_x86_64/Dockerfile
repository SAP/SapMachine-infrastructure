#
# Alpine based Docker image for building OpenJDK/SapMachine on and for Alpine Linux
#

FROM alpine:3.5

RUN apk update; \
    apk add bash; \
    apk add file; \
    apk add grep; \
    apk add make; \
    apk add zip; \
    apk add tar; \
    apk add musl-dev; \
    apk add gcc; \
    apk add g++; \
    apk add libx11-dev; \
    apk add libxext-dev; \
    apk add libxrender-dev; \
    apk add libxtst-dev; \
    apk add libxt-dev; \
    apk add cups-dev; \
    apk add fontconfig-dev; \
    apk add alsa-lib-dev; \
    apk add linux-headers; \
    apk add git; \
    apk add mercurial; \
    apk add ttf-dejavu; \
    apk add sed; \
    apk add --update openssl; \
    apk add patch; \
    mkdir /opt; \
    cd /opt; \
    wget 'https://github.com/SAP/SapMachine/releases/download/sapmachine-10+39/sapmachine-jdk-10-ea.39_linux-x64-musl_bin.tar.gz'; \
    tar -xzf 'sapmachine-jdk-10-ea.39_linux-x64-musl_bin.tar.gz'; \
    rm 'sapmachine-jdk-10-ea.39_linux-x64-musl_bin.tar.gz'

ENV PATH=/opt/sapmachine-jdk-10/bin:$PATH

RUN addgroup -g 1002 jenkins && \
    adduser -D -u 1002 -G jenkins jenkins

RUN mkdir -p /opt/scimark2
RUN wget https://math.nist.gov/scimark2/scimark2lib.jar -O /opt/scimark2/scimark2lib.jar
