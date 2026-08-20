FROM ubuntu:24.04

RUN apt-get update && \
    apt-get -y --no-install-recommends install ca-certificates gnupg && \
    export GNUPGHOME="$(mktemp -d)" && \
    gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/sapmachine.gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys CACB9FE09150307D1D22D82962754C3B3ABCFE23 && \
    chmod 644 /usr/share/keyrings/sapmachine.gpg && \
    { \
        echo 'Types: deb'; \
        echo 'URIs: https://dist.sapmachine.io/debian'; \
        echo 'Suites: stable'; \
        echo 'Components: main'; \
        echo 'Architectures: amd64 arm64 ppc64el'; \
        echo 'Signed-By: /usr/share/keyrings/sapmachine.gpg'; \
    } > /etc/apt/sources.list.d/sapmachine.sources && \
    apt-get update && \
    apt-get -y --no-install-recommends install sapmachine-25-jdk-headless=25.0.4.1 && \
    apt-get remove -y --purge --autoremove ca-certificates gnupg && \
    rm -rf "$GNUPGHOME" /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-25

CMD ["jshell"]
