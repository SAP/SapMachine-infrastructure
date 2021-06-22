FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

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
ant \
patch \
mercurial \
openjdk-8-jdk

RUN useradd -ms /bin/bash jenkins -u 1002
