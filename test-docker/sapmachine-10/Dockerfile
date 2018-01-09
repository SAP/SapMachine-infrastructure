
FROM ubuntu:16.04

MAINTAINER Sapmachine <sapmachine@sap.com>

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates zip git unzip realpath python \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - http://sapmachine-ubuntu.sapcloud.io/sapmachine-debian.key | apt-key add - \
    && echo "deb http://sapmachine-ubuntu.sapcloud.io/amd64/ ./" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get -y --no-install-recommends install sapmachine-10-jre=10+37

