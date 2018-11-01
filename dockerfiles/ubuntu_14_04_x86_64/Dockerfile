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
bsdtar \
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

RUN useradd -ms /bin/bash jenkins -u 1002

RUN mkdir -p /opt/sapmachine-11-jdk
ENV BOOT_JDK=/opt/sapmachine-11-jdk
WORKDIR $BOOT_JDK
RUN wget -q https://github.com/SAP/SapMachine/releases/download/sapmachine-11.0.1%2B13-0/sapmachine-jdk-11.0.1.13_linux-x64_bin.tar.gz
RUN bsdtar xf sapmachine-jdk-11.0.1.13_linux-x64_bin.tar.gz --strip-components=1

RUN mkdir -p /opt/scimark2
RUN wget https://math.nist.gov/scimark2/scimark2lib.jar -O /opt/scimark2/scimark2lib.jar

ADD sysroot-sles11-x86_64.tgz /opt
ENV _CONFIGURE_SYSROOT="--with-sysroot=/opt/sysroot-sles11-x86_64 --with-freetype-lib=/opt/sysroot-sles11-x86_64/usr/lib64 --with-freetype-include=/opt/sysroot-sles11-x86_64/usr/include --with-stdc++lib=static"

WORKDIR /opt
RUN wget https://mirrors.kernel.org/gnu/gcc/gcc-7.3.0/gcc-7.3.0.tar.gz && \
    tar xzf gcc-7.3.0.tar.gz && \
    mkdir /opt/gcc-build && \
    mkdir /opt/gcc-7.3.0-bin

WORKDIR /opt/gcc-build
RUN /opt/gcc-7.3.0/configure --enable-languages=c,c++ --prefix=/opt/gcc-7.3.0-bin --disable-multilib --with-build-sysroot=/opt/sysroot-sles11-x86_64 && \
    make -j$(grep -c ^processor /proc/cpuinfo) && \
    make install && \
    rm -rf /opt/gcc-7.3.0 && \
    rm -rf /opt/gcc-build

ENV PATH="/opt/gcc-7.3.0-bin/bin:${PATH}"
WORKDIR /
