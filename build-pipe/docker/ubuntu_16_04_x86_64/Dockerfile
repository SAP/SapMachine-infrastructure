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
graphviz

RUN mkdir -p /opt/openjdk-9-jdk
ENV BOOT_JDK=/opt/openjdk-9-jdk
WORKDIR $BOOT_JDK
RUN wget -q https://github.com/SAP/SapMachine/releases/download/sapmachine-10.0.1%2B10-0/sapmachine-jdk-10.0.1.10_linux-x64_bin.tar.gz
RUN bsdtar xf sapmachine-jdk-10.0.1.10_linux-x64_bin.tar.gz --strip-components=1

RUN mkdir -p /opt/github-release
WORKDIR /opt/github-release
RUN wget -q https://github.com/aktau/github-release/releases/download/v0.7.2/linux-amd64-github-release.tar.bz2
RUN bunzip2 linux-amd64-github-release.tar.bz2
RUN bsdtar xf linux-amd64-github-release.tar --strip-components=3
RUN ln -s /opt/github-release/github-release /usr/bin/github-release
