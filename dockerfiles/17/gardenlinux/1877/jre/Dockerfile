FROM ghcr.io/gardenlinux/gardenlinux:1877

ADD --chmod=644 --chown=root:root https://dist.sapmachine.io/debian/sapmachine.key /etc/apt/trusted.gpg.d/sapmachine.asc

RUN echo "deb https://dist.sapmachine.io/debian/$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-17-jre=17.0.17 && \
    rm -rf /var/lib/apt/lists/* && \
    java -version

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-17

CMD ["bash"]
