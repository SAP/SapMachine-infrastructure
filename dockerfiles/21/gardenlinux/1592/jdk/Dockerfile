FROM ghcr.io/gardenlinux/gardenlinux:1592.20

ENV LANG=C.UTF-8
ENV JAVA_VERSION=21.0.11
ENV MALLOC_ARENA_MAX=1

ADD --chmod=644 --chown=root:root https://dist.sapmachine.io/debian/sapmachine.key /etc/apt/trusted.gpg.d/sapmachine.asc

RUN echo "deb https://dist.sapmachine.io/debian/$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-21-jdk=21.0.11 && \
    rm -rf /var/lib/apt/lists/* && \
    java -XshowSettings:properties -version

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-21

CMD ["jshell"]
