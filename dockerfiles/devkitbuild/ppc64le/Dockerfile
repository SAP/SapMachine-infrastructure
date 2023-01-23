FROM ubuntu:20.04

ARG ARTIFACTORY_CREDS

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
autoconf \
ca-certificates \
cpio \
gcc \
git \
g++ \
make \
rpm2cpio \
texinfo \
wget \
xz-utils

WORKDIR /devkit

RUN git clone --depth 1 -b sapmachine17 https://github.com/SAP/SapMachine.git && mv SapMachine/make/devkit . && rm -rf SapMachine && mkdir -p SapMachine/make && mv devkit SapMachine/make

WORKDIR /devkit/SapMachine/build/devkit/download/rpms/ppc64le-linux-gnu-Fedora_19

RUN wget --no-verbose --show-progress --progress=bar:force:noscroll https://$ARTIFACTORY_CREDS@common.repositories.cloud.sap/artifactory/sapmachine-mvn/io/sapmachine/build/devkit/linux-ppc64le/rpms/7/rpms-7.tar.gz 2>&1 && tar --no-same-permissions --no-same-owner -xzf rpms-7.tar.gz && rm rpms-7.tar.gz

WORKDIR /devkit/SapMachine/make/devkit

RUN make BASE_OS=Fedora BASE_OS_VERSION=19 GCC_VER=8.3.0 tars && mv /devkit/SapMachine/build/devkit/result/*.tar.gz /devkit && rm -rf /devkit/SapMachine

WORKDIR /devkit
