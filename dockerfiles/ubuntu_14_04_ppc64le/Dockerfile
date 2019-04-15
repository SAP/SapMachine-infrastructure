FROM ubuntu:14.04

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
realpath \
libfontconfig1-dev \
ca-certificates \
curl \
pandoc \
graphviz \
python \
ant \
patch \
mercurial \
openjdk-7-jdk \
libgmp-dev \
libmpfr-dev \
libmpc-dev

RUN useradd -ms /bin/bash jenkinsa -u 1000
RUN useradd -ms /bin/bash jenkinsb -u 1001
RUN useradd -ms /bin/bash jenkinsc -u 1002

RUN mkdir -p /opt/scimark2
RUN wget https://math.nist.gov/scimark2/scimark2lib.jar -O /opt/scimark2/scimark2lib.jar

ADD sysroot-sles12-ppc64le.tgz /opt

WORKDIR /opt
RUN wget https://mirrors.kernel.org/gnu/gcc/gcc-7.3.0/gcc-7.3.0.tar.gz && \
    tar xzf gcc-7.3.0.tar.gz && \
    mkdir /opt/gcc-build && \
    mkdir /opt/gcc-7.3.0-bin

WORKDIR /opt/gcc-build
RUN /opt/gcc-7.3.0/configure --enable-languages=c,c++ --prefix=/opt/gcc-7.3.0-bin --disable-multilib --with-build-sysroot=/opt/sysroot-sles12-ppc64le && \
    make -j$(grep -c ^processor /proc/cpuinfo) && \
    make install && \
    rm -rf /opt/gcc-7.3.0 && \
    rm -rf /opt/gcc-build

ENV PATH="/opt/gcc-7.3.0-bin/bin:${PATH}"

WORKDIR /
