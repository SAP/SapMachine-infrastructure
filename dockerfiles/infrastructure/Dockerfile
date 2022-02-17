FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
zip \
wget \
ca-certificates \
curl \
git \
unzip \
python3 \
python3-setuptools \
python3-pip \
python3-dev \
libffi-dev \
openssl \
libssl-dev \
gcc \
g++ \
maven \
gpg \
gpg-agent

RUN useradd -ms /bin/bash jenkins -u 1002

RUN pip3 install wheel
RUN pip3 install jenkins-job-builder
RUN pip3 install jenkinsapi
RUN pip3 install pyyaml
RUN pip3 install requests
