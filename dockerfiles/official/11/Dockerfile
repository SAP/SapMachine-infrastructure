
FROM ubuntu:18.04

MAINTAINER Rene Schuenemann <sapmachine@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates gnupg2 \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dist.sapmachine.io/debian/sapmachine.key | apt-key add - \
    && echo "deb http://dist.sapmachine.io/debian/amd64/ ./" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get -y --no-install-recommends install sapmachine-11-jdk=11.0.2


