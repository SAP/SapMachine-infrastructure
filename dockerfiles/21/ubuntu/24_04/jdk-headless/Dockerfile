FROM ubuntu:24.04

RUN apt-get update && \
    apt-get -y --no-install-recommends install ca-certificates gnupg wget && \
    export GNUPGHOME="$(mktemp -d)" && \
    gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/sapmachine.gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys CACB9FE09150307D1D22D82962754C3B3ABCFE23 && \
    chmod 644 /usr/share/keyrings/sapmachine.gpg && \
    wget -qO /etc/apt/sources.list.d/sapmachine.sources \
      https://dist.sapmachine.io/debian/sapmachine.sources && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-21-jdk-headless=21.0.12 && \
    apt-get remove -y --purge --autoremove ca-certificates gnupg wget && \
    rm -rf "$GNUPGHOME" /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-21

CMD ["jshell"]
