FROM ghcr.io/gardenlinux/gardenlinux:2150.8.0

ENV LANG=C.UTF-8
ENV JAVA_VERSION=17.0.20.1
ENV MALLOC_ARENA_MAX=1

RUN apt-get update && \
    apt-get -y --no-install-recommends install wget gnupg && \
    wget -qO /usr/share/keyrings/sapmachine.gpg \
      https://dist.sapmachine.io/debian/sapmachine.gpg && \
    wget -qO /etc/apt/sources.list.d/sapmachine.sources \
      https://dist.sapmachine.io/debian/sapmachine.sources && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-17-jdk-headless=17.0.20.1 && \
    apt-get remove -y --purge --autoremove wget gnupg && \
    rm -rf /var/lib/apt/lists/* && \
    java -XshowSettings:properties -version

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-17

CMD ["jshell"]
