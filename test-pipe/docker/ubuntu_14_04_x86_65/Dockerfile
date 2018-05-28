FROM ubuntu:14.04

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
make \
gcc \
g++ \
zip \
wget \
git \
unzip \
realpath \
ca-certificates \
curl \
python \
mercurial \
openjdk-7-jdk \
ant \
patch

RUN useradd -ms /bin/bash jenkins -u 1002

RUN mkdir -p /opt/scimark2
RUN wget https://math.nist.gov/scimark2/scimark2lib.jar -O /opt/scimark2/scimark2lib.jar
