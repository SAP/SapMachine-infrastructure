FROM ubuntu:16.04

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
dh-make \
devscripts \
python \
git \
ca-certificates \
fakeroot \
make \
gcc \
g++ \
build-essential \
openjdk-8-jdk \
openssh-client

RUN useradd -ms /bin/bash jenkins -u 1001