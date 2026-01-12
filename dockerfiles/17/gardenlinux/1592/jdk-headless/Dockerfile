FROM ghcr.io/gardenlinux/gardenlinux:1592

ADD --chmod=644 --chown=root:root https://dist.sapmachine.io/debian/sapmachine.key /etc/apt/trusted.gpg.d/sapmachine.asc

RUN echo "deb https://dist.sapmachine.io/debian/$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-17-jdk-headless=17.0.17 && \
    apt-get remove -y --purge --autoremove wget && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-17

CMD ["jshell"]
