
FROM ubuntu:16.04

MAINTAINER Rene Schuenemann <sapmachine@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dist.sapmachine.io/debian/sapmachine.key | apt-key add - \
    && echo "deb http://dist.sapmachine.io/debian/amd64/ ./" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get -y --no-install-recommends install sapmachine-12-jdk=12+24.0


