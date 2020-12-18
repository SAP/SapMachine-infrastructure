
FROM ubuntu:20.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates gnupg2 \
    && rm -rf /var/lib/apt/lists/*

RUN if [ `uname -m` = "aarch64" ] ; then \
       wget -q  https://github.com/SAP/SapMachine/releases/download/sapmachine-15.0.1/sapmachine-jdk-15.0.1-beta_linux-aarch64_bin.tar.gz && \
       tar -xf /sapmachine-jdk-15.0.1-beta_linux-aarch64_bin.tar.gz && \
       mkdir /usr/lib/jvm && \
       cp -R sapmachine-jdk-15.0.1 /usr/lib/jvm/sapmachine-15 && \
       rm /sapmachine-jdk-15.0.1-beta_linux-aarch64_bin.tar.gz; \
    else \
       export GNUPGHOME="$(mktemp -d)" && \
       wget -q -O - https://dist.sapmachine.io/debian/sapmachine.old.key | gpg --batch --import && \
       gpg --batch --export --armor 'DA4C 00C1 BDB1 3763 8608 4E20 C7EB 4578 740A EEA2' > /etc/apt/trusted.gpg.d/sapmachine.old.gpg.asc && \
       wget -q -O - https://dist.sapmachine.io/debian/sapmachine.key | gpg --batch --import && \
       gpg --batch --export --armor 'CACB 9FE0 9150 307D 1D22 D829 6275 4C3B 3ABC FE23' > /etc/apt/trusted.gpg.d/sapmachine.gpg.asc && \
       gpgconf --kill all && rm -rf "$GNUPGHOME" && \
       echo "deb http://dist.sapmachine.io/debian/amd64/ ./" > /etc/apt/sources.list.d/sapmachine.list && \
       apt-get update && \
       apt-get -y --no-install-recommends install sapmachine-15-jdk=15.0.1 && \
       rm -rf /var/lib/apt/lists/*; \
    fi

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-15
ENV PATH=$PATH:$JAVA_HOME/bin

CMD ["jshell"]
