FROM sapmachine:11

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
wget \
ca-certificates \
openssl \
maven \
gpg \
gpg-agent

RUN useradd -ms /bin/bash jenkins -u 1002
