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
    apk add alpine-sdk;

RUN mkdir -p /var/cache/distfiles
RUN chmod a+w /var/cache/distfiles

RUN useradd -ms /bin/bash jenkins -u 1001
RUN addgroup jenkins abuild
RUN echo "jenkins    ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER jenkins
RUN abuild-keygen -a -i -n
