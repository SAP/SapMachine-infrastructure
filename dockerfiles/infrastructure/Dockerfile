FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
zip \
wget \
ca-certificates \
curl \
git \
mercurial \
unzip \
python3 \
python3-setuptools \
python3-pip \
python3-dev \
libffi-dev \
openssl \
libssl-dev \
gcc \
g++

RUN useradd -ms /bin/bash jenkins -u 1002

RUN pip3 install wheel
RUN pip3 install hg-git==0.9.0a1
RUN pip3 install mercurial
RUN echo "[extensions]\nhgext.bookmarks =\nhggit =" > /etc/mercurial/hgrc

RUN cd ~ && git clone https://github.com/reshnm/git-hg-again.git && cp git-hg-again/githg.py  /usr/lib/git-core/git-hg

RUN pip3 install jenkins-job-builder
RUN pip3 install jenkinsapi
RUN pip3 install pyyaml
