FROM ghcr.io/gardenlinux/gardenlinux:1877.22

ENV LANG=C.UTF-8
ENV JAVA_VERSION=21.0.12.1
ENV MALLOC_ARENA_MAX=1

RUN apt-get update && \
    apt-get -y --no-install-recommends install wget gnupg && \
    wget -qO /usr/share/keyrings/sapmachine.gpg \
      https://dist.sapmachine.io/debian/sapmachine.gpg && \
    wget -qO /etc/apt/sources.list.d/sapmachine.sources \
      https://dist.sapmachine.io/debian/sapmachine.sources && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-21-jre=21.0.12.1 && \
    apt-get remove -y --purge --autoremove wget gnupg && \
    rm -rf /var/lib/apt/lists/* && \
    java -XshowSettings:properties -version

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-21

CMD ["bash"]
