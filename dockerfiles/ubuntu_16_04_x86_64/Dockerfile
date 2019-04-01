FROM ubuntu:16.04

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
cpio \
make \
gcc \
g++ \
autoconf \
file \
libx11-dev \
libxext-dev \
libxrender-dev \
libxtst-dev \
libxt-dev \
libxrandr-dev \
libelf-dev \
libcups2-dev \
libfreetype6-dev \
libasound2-dev \
ccache \
zip \
wget \
git \
unzip \
realpath \
libfontconfig1-dev \
ca-certificates \
curl \
pandoc \
graphviz \
python \
ant \
patch \
mercurial \
openjdk-8-jdk

RUN useradd -ms /bin/bash jenkins -u 1002

RUN mkdir -p /opt/scimark2
RUN wget https://math.nist.gov/scimark2/scimark2lib.jar -O /opt/scimark2/scimark2lib.jar

RUN mkdir -p /opt/dacapo
RUN wget https://sourceforge.net/projects/dacapobench/files/9.12-bach-MR1/dacapo-9.12-MR1-bach.jar/download -O /opt/dacapo/dacapo.jar
