FROM ubuntu:20.04

ARG ARTIFACTORY_CREDS
ARG DEVKIT_NAME=devkit-fedora-gcc
ARG DEVKIT_VERSION=21-8.3.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
autoconf \
build-essential \
ca-certificates \
cpio \
curl \
dh-make \
devscripts \
file \
git \
libasound2-dev \
libcups2-dev \
libelf-dev \
libfontconfig1-dev \
libfreetype6-dev \
libx11-dev \
libxext-dev \
libxrandr-dev \
libxrender-dev \
libxt-dev \
libxtst-dev \
make \
python3 \
python3-pip \
unzip \
wget \
zip

RUN useradd -ms /bin/bash jenkinsa -u 1000
RUN useradd -ms /bin/bash jenkinsb -u 1001
RUN useradd -ms /bin/bash jenkinsc -u 1002

RUN pip3 install requests

WORKDIR /opt/devkits
RUN wget --no-verbose --show-progress --progress=bar:force:noscroll https://$ARTIFACTORY_CREDS@common.repositories.cloud.sap/artifactory/sapmachine-mvn/io/sapmachine/build/devkit/linux-aarch64/${DEVKIT_NAME}/${DEVKIT_VERSION}/${DEVKIT_NAME}-${DEVKIT_VERSION}.tar.gz 2>&1
WORKDIR /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION}
RUN tar xzf ../${DEVKIT_NAME}-${DEVKIT_VERSION}.tar.gz

WORKDIR /tmp
ADD https://raw.githubusercontent.com/tstuefe/tinyreaper/master/tinyreaper.c /tmp/
RUN /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION}/bin/gcc -I/usr/include -I/usr/include/aarch64-linux-gnu /tmp/tinyreaper.c -o /opt/tinyreaper && \
    chmod +x /opt/tinyreaper && \
    rm /tmp/tinyreaper.c
