FROM sapmachine:11 AS sapmachine

FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
git \
zip \
unzip \
ca-certificates \
wget \
make

COPY --from=sapmachine /usr/lib/jvm/sapmachine-11 /usr/lib/jvm

RUN useradd -ms /bin/bash jenkins -u 1002
