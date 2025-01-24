FROM alpine:3.21

RUN wget -qO /etc/apk/keys/sapmachine-apk.rsa.pub https://dist.sapmachine.io/alpine/sapmachine-apk.rsa.pub \
    && echo "https://dist.sapmachine.io/alpine" >> /etc/apk/repositories \
    && apk add sapmachine-23-jre=23.0.2-r0

ENV JAVA_HOME=/usr/lib/jvm/java-23-sapmachine-jre

CMD ["jshell"]
