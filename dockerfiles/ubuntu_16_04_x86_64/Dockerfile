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
bsdtar \
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

RUN mkdir -p /opt/sapmachine-10-jdk
ENV BOOT_JDK=/opt/sapmachine-10-jdk
WORKDIR $BOOT_JDK
RUN wget -q https://github.com/SAP/SapMachine/releases/download/sapmachine-10.0.1%2B10-0/sapmachine-jdk-10.0.1.10_linux-x64_bin.tar.gz
RUN bsdtar xf sapmachine-jdk-10.0.1.10_linux-x64_bin.tar.gz --strip-components=1

RUN mkdir -p /opt/scimark2
RUN wget https://math.nist.gov/scimark2/scimark2lib.jar -O /opt/scimark2/scimark2lib.jar
