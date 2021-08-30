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
openjdk-11-jdk \
libgmp-dev \
libmpfr-dev \
libmpc-dev

RUN useradd -ms /bin/bash jenkinsa -u 1000
RUN useradd -ms /bin/bash jenkinsb -u 1001
RUN useradd -ms /bin/bash jenkinsc -u 1002

ADD sysroot-sles11-x86_64.tgz /opt

WORKDIR /opt
RUN wget https://mirrors.kernel.org/gnu/gcc/gcc-8.4.0/gcc-8.4.0.tar.gz && \
    tar xzf gcc-8.4.0.tar.gz && \
    mkdir /opt/gcc-build && \
    mkdir /opt/gcc-8.4.0-bin

WORKDIR /opt/gcc-build
RUN /opt/gcc-8.4.0/configure --enable-languages=c,c++ --prefix=/opt/gcc-8.4.0-bin --disable-multilib --enable-multiarch --with-build-sysroot=/opt/sysroot-sles11-x86_64 && \
    make -j$(grep -c ^processor /proc/cpuinfo) && \
    make install && \
    rm -rf /opt/gcc-8.4.0 && \
    rm -rf /opt/gcc-build

ENV PATH="/opt/gcc-8.4.0-bin/bin:${PATH}"

WORKDIR /
