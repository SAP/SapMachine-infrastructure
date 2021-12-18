FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
git \
zip \
unzip \
ca-certificates \
curl \
wget \
make \
openjdk-8-jdk

RUN useradd -ms /bin/bash jenkins -u 1002
