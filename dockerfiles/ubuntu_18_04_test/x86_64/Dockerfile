FROM ubuntu:18.04

ARG ARTIFACTORY_USER
ARG ARTIFACTORY_PASSWORD
ARG DEVKIT_NAME=devkit-fedora-gcc
ARG DEVKIT_VERSION=12-8.3.0

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
libfontconfig1-dev \
ca-certificates \
curl \
pandoc \
graphviz \
python3 \
python3-pip \
ant \
bison \
flex \
patch \
mercurial \
openjdk-11-jdk \
libgmp-dev \
libmpfr-dev \
libmpc-dev

RUN useradd -ms /bin/bash jenkinsa -u 1000
RUN useradd -ms /bin/bash jenkinsb -u 1001
RUN useradd -ms /bin/bash jenkinsc -u 1002

RUN pip3 install requests

WORKDIR /opt/devkits
ADD https://$ARTIFACTORY_USER:$ARTIFACTORY_PASSWORD@common.repositories.cloud.sap/artifactory/sapmachine-mvn/io/sapmachine/build/devkit/linux-x64/${DEVKIT_NAME}/${DEVKIT_VERSION}/${DEVKIT_NAME}-${DEVKIT_VERSION}.tar.gz /opt/devkits/
WORKDIR /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION}
RUN tar xvzf ../${DEVKIT_NAME}-${DEVKIT_VERSION}.tar.gz

WORKDIR /tmp
ADD https://raw.githubusercontent.com/tstuefe/tinyreaper/master/tinyreaper.c /tmp/
RUN gcc /tmp/tinyreaper.c -o /opt/tinyreaper && \
    chmod +x /opt/tinyreaper && \
    rm /tmp/tinyreaper.c
