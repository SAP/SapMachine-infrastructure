FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
autoconf \
build-essential \
ca-certificates \
cpio \
curl \
file \
gcc \
g++ \
git \
libelf-dev \
make \
rpm2cpio \
unzip \
wget \
zip

WORKDIR /devkit

RUN git clone -b sapmachinedevkit17 https://github.com/RealCLanger/SapMachine.git

WORKDIR /devkit/SapMachine/make/devkit

RUN make BASE_OS=Fedora BASE_OS_VERSION=21 GCC_VER=8.3.0 tars
