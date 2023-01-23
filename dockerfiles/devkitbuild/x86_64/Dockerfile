FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
autoconf \
ca-certificates \
cpio \
gcc \
gcc-multilib \
git \
g++ \
make \
rpm2cpio \
texinfo \
wget \
xz-utils

WORKDIR /devkit

RUN git clone --depth 1 -b sapmachinedevkit17 https://github.com/RealCLanger/SapMachine.git && mv SapMachine/make/devkit . && rm -rf SapMachine && mkdir -p SapMachine/make && mv devkit SapMachine/make

WORKDIR /devkit/SapMachine/make/devkit

RUN make BASE_OS=Fedora BASE_OS_VERSION=19 GCC_VER=8.3.0 tars
