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
openjdk-7-jdk

RUN mkdir -p /opt/openjdk-10-jdk
ENV BOOT_JDK=/opt/openjdk-10-jdk
WORKDIR $BOOT_JDK
RUN wget -q https://github.com/AdoptOpenJDK/openjdk10-releases/releases/download/201807101745/OpenJDK10_ppc64le_Linux_201807101745.tar.gz
RUN bsdtar xf OpenJDK10_ppc64le_Linux_201807101745.tar.gz --strip-components=2
