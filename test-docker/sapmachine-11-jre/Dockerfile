
FROM ubuntu:16.04

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates zip git unzip realpath python binutils \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dist.sapmachine.io/debian/sapmachine.key | apt-key add - \
    && echo "deb http://dist.sapmachine.io/debian/amd64/ ./" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get -y --no-install-recommends install sapmachine-11-jre=11+7.0

RUN useradd -ms /bin/bash jenkins -u 1002

