
FROM ubuntu:16.04

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://sapmachine-ubuntu.sapcloud.io/debian/sapmachine-debian.key | apt-key add - \
    && echo "deb http://sapmachine-ubuntu.sapcloud.io/debian/amd64/ ./" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get -y --no-install-recommends install sapmachine-10-jdk=10+42.0



