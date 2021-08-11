FROM ubuntu:18.04

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
bison \
flex \
patch \
mercurial \
openjdk-8-jdk \
libgmp-dev \
libmpfr-dev \
libmpc-dev

RUN useradd -ms /bin/bash jenkinsa -u 1000
RUN useradd -ms /bin/bash jenkinsb -u 1001
RUN useradd -ms /bin/bash jenkinsc -u 1002

ADD sysroot-sles12-ppc64le.tgz /opt

# we cannot use gcc-8 / g++-8 from the package installation, it does not work with our sysroot
# and using without sysroot creates a JDK that does not work on SLES12 SP1

WORKDIR /
