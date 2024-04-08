FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
ca-certificates \
curl \
g++ \
gcc \
git \
gpg \
gpg-agent \
libffi-dev \
libssl-dev \
maven \
openssl \
python3 \
python3-dev \
python3-pip \
python3-setuptools \
tzdata \
unzip \
wget \
zip

RUN useradd -ms /bin/bash jenkins -u 1002

RUN pip3 install wheel "urllib3<2" jenkins-job-builder jenkinsapi pyyaml requests
