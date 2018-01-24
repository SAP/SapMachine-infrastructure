FROM alpine:3.5

MAINTAINER Sapmachine <sapmachine@sap.com>

RUN apk update; \
    apk add bash; \
    apk add file; \
    apk add grep; \
    apk add make; \
    apk add zip; \
    apk add tar; \
    apk add python; \
    apk add git; \
    apk add shadow; \
    apk add openssh; \
    apk add alpine-sdk;

RUN mkdir -p /var/cache/distfiles
RUN chmod a+w /var/cache/distfiles

RUN groupadd -g 1001 jenkins
RUN useradd -ms /bin/bash jenkins -u 1001 -g 1001 -G abuild
RUN echo "jenkins    ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN echo "PACKAGER=\"SapMachine <sapmachine@sap.com>\"" >> /etc/abuild.conf
RUN echo "MAINTAINER=\"$PACKAGER\"" >> /etc/abuild.conf

USER jenkins
RUN abuild-keygen -a -i -n
