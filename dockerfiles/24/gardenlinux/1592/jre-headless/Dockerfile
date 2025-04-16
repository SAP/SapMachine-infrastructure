FROM ghcr.io/gardenlinux/gardenlinux:1592

RUN apt-get update && \
    apt-get -y --no-install-recommends install wget && \
    wget -qO- https://dist.sapmachine.io/debian/sapmachine.key > /etc/apt/trusted.gpg.d/sapmachine.asc && \
    chmod 644 /etc/apt/trusted.gpg.d/sapmachine.asc && \
    echo "deb https://dist.sapmachine.io/debian/$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-24-jre-headless=24.0.1 && \
    apt-get remove -y --purge --autoremove wget && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-24

CMD ["jshell"]
