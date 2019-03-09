FROM ubuntu:16.04

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
zip \
wget \
ca-certificates \
curl \
git \
mercurial \
unzip \
realpath \
python \
python-dev \
python-pip \
python-setuptools \
libffi-dev \
openssl \
libssl-dev \
gcc \
g++

RUN useradd -ms /bin/bash jenkins -u 1002

RUN easy_install hg-git
RUN echo "[extensions]\nhgext.bookmarks =\nhggit =" > /etc/mercurial/hgrc

RUN cd ~ && git clone https://github.com/reshnm/git-hg-again.git && cp git-hg-again/githg.py  /usr/lib/git-core/git-hg

RUN pip install jenkins-job-builder
RUN pip install jenkinsapi
RUN pip install pyyaml
