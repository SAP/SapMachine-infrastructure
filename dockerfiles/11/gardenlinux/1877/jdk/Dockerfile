FROM ghcr.io/gardenlinux/gardenlinux:1877

ENV LANG=C.UTF-8
ENV JAVA_VERSION=11.0.30
ENV MALLOC_ARENA_MAX=1

ADD --chmod=644 --chown=root:root https://dist.sapmachine.io/debian/sapmachine.key /etc/apt/trusted.gpg.d/sapmachine.asc

RUN echo "deb https://dist.sapmachine.io/debian/$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-11-jdk=11.0.30 && \
    rm -rf /var/lib/apt/lists/* && \
    java -XshowSettings:properties -version

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-11

CMD ["jshell"]
