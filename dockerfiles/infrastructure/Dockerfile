FROM ubuntu:18.04

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
zip \
wget \
ca-certificates \
curl \
git \
mercurial \
unzip \
python \
python-setuptools \
python-pip \
python3 \
python3-setuptools \
python3-pip \
libffi-dev \
openssl \
libssl-dev \
gcc \
g++

RUN useradd -ms /bin/bash jenkins -u 1002

RUN pip install hg-git
RUN echo "[extensions]\nhgext.bookmarks =\nhggit =" > /etc/mercurial/hgrc

RUN cd ~ && git clone https://github.com/reshnm/git-hg-again.git && cp git-hg-again/githg.py  /usr/lib/git-core/git-hg

RUN pip3 install jenkins-job-builder
RUN pip3 install jenkinsapi
RUN pip3 install pyyaml
