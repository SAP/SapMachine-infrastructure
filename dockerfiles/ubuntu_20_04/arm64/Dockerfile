FROM ubuntu:20.04

ARG ARTIFACTORY_CREDS
ARG DEVKIT_NAME=devkit-fedora-gcc
ARG DEVKIT_VERSION=21-8.5.0
ARG DEVKIT_VERSION_2=21-10.3.0
ARG DEVKIT_VERSION_3=27-11.3.0

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
autoconf \
build-essential \
ca-certificates \
cpio \
curl \
dh-make \
devscripts \
fakeroot \
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

# Add some users for ids that are used by jenkins docker containers
# This is necessary for some things to work, e.g. git config --global
RUN useradd -ms /bin/bash jenkinse -u 1000
RUN useradd -ms /bin/bash jenkinsi -u 50050

RUN pip3 install requests

WORKDIR /opt/devkits

RUN wget --no-verbose --show-progress --progress=bar:force:noscroll https://$ARTIFACTORY_CREDS@common.repositories.cloud.sap/artifactory/sapmachine-mvn/io/sapmachine/build/devkit/linux-aarch64/${DEVKIT_NAME}/${DEVKIT_VERSION}/${DEVKIT_NAME}-${DEVKIT_VERSION}.tar.gz 2>&1 && \
  mkdir ${DEVKIT_NAME}-${DEVKIT_VERSION} && cd ${DEVKIT_NAME}-${DEVKIT_VERSION} && \
  tar --no-same-permissions --no-same-owner --strip-components=1 -xzf ../${DEVKIT_NAME}-${DEVKIT_VERSION}.tar.gz && \
  rm ../${DEVKIT_NAME}-${DEVKIT_VERSION}.tar.gz && \
  chmod 755 $(find /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION} -type d) && \
  chmod u+r,g+r,a+r $(find /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION} -type f)

RUN wget --no-verbose --show-progress --progress=bar:force:noscroll https://$ARTIFACTORY_CREDS@common.repositories.cloud.sap/artifactory/sapmachine-mvn/io/sapmachine/build/devkit/linux-aarch64/${DEVKIT_NAME}/${DEVKIT_VERSION_2}/${DEVKIT_NAME}-${DEVKIT_VERSION_2}.tar.gz 2>&1 && \
  mkdir ${DEVKIT_NAME}-${DEVKIT_VERSION_2} && cd ${DEVKIT_NAME}-${DEVKIT_VERSION_2} && \
  tar --no-same-permissions --no-same-owner --strip-components=1 -xzf ../${DEVKIT_NAME}-${DEVKIT_VERSION_2}.tar.gz && \
  rm ../${DEVKIT_NAME}-${DEVKIT_VERSION_2}.tar.gz && \
  chmod 755 $(find /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION_2} -type d) && \
  chmod u+r,g+r,a+r $(find /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION_2} -type f)

RUN wget --no-verbose --show-progress --progress=bar:force:noscroll https://$ARTIFACTORY_CREDS@common.repositories.cloud.sap/artifactory/sapmachine-mvn/io/sapmachine/build/devkit/linux-aarch64/${DEVKIT_NAME}/${DEVKIT_VERSION_3}/${DEVKIT_NAME}-${DEVKIT_VERSION_3}.tar.gz 2>&1 && \
  mkdir ${DEVKIT_NAME}-${DEVKIT_VERSION_3} && cd ${DEVKIT_NAME}-${DEVKIT_VERSION_3} && \
  tar --no-same-permissions --no-same-owner --strip-components=1 -xzf ../${DEVKIT_NAME}-${DEVKIT_VERSION_3}.tar.gz && \
  rm ../${DEVKIT_NAME}-${DEVKIT_VERSION_3}.tar.gz && \
  chmod 755 $(find /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION_3} -type d) && \
  chmod u+r,g+r,a+r $(find /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION_3} -type f)

WORKDIR /tmp
ADD https://raw.githubusercontent.com/tstuefe/tinyreaper/master/tinyreaper.c /tmp/
RUN /opt/devkits/${DEVKIT_NAME}-${DEVKIT_VERSION}/bin/gcc -I/usr/include -I/usr/include/aarch64-linux-gnu /tmp/tinyreaper.c -o /opt/tinyreaper && \
    chmod +x /opt/tinyreaper && \
    rm /tmp/tinyreaper.c
