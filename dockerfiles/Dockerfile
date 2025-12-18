ARG GARDEN_LINUX_MAJOR_VER
ARG SAPMACHINE_MAJOR_VER
ARG SAPMACHINE_FLAVOR

# Base image used in all further stages
FROM ghcr.io/gardenlinux/gardenlinux:$GARDEN_LINUX_MAJOR_VER as base-stage
RUN apt-get update && apt-get -y --no-install-recommends install wget && \
    wget -qO- https://dist.sapmachine.io/debian/sapmachine.key > /etc/apt/trusted.gpg.d/sapmachine.asc && \
    chmod 644 /etc/apt/trusted.gpg.d/sapmachine.asc && \
    echo "deb https://dist.sapmachine.io/debian/$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list && \
    apt-get update

# TODO: do checksum verification via debian repository
# https://dist.sapmachine.io/debian/amd64/Packages

# Image to calculate and export checksum.
FROM base-stage as checksum-stage
ARG SAPMACHINE_MAJOR_VER
ARG SAPMACHINE_FLAVOR
RUN apt download -y sapmachine-$SAPMACHINE_MAJOR_VER-$SAPMACHINE_FLAVOR
RUN echo -n "md5:" > checksum.txt
RUN md5sum sapmachine-$SAPMACHINE_MAJOR_VER-$SAPMACHINE_FLAVOR*.deb | awk '{ print $1 }' >> checksum.txt


# Final image
FROM base-stage as main-stage
ARG SAPMACHINE_MAJOR_VER
ARG SAPMACHINE_FLAVOR
ARG SAPMACHINE_CHECKSUM
ARG GARDEN_LINUX_IMAGEID
LABEL sapmachine.checksum=$SAPMACHINE_CHECKSUM
LABEL gardenlinux.id=$GARDEN_LINUX_IMAGEID
RUN apt-get -y --no-install-recommends install sapmachine-$SAPMACHINE_MAJOR_VER-$SAPMACHINE_FLAVOR
RUN apt-get remove -y --purge --autoremove wget && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/sapmachine-24

CMD ["jshell"]
