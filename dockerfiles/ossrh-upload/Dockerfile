FROM maven:3-sapmachine-11

RUN apt-get update && apt-get install -qq -y --no-install-recommends gpg gpg-agent

RUN useradd -ms /bin/bash jenkins -u 1002
