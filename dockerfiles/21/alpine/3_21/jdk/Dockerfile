FROM alpine:3.21

RUN wget -qO /etc/apk/keys/sapmachine-apk.rsa.pub https://dist.sapmachine.io/alpine/sapmachine-apk.rsa.pub \
    && echo "https://dist.sapmachine.io/alpine" >> /etc/apk/repositories \
    && apk add sapmachine-21-jdk=21.0.5-r0

ENV JAVA_HOME=/usr/lib/jvm/java-21-sapmachine-jdk

CMD ["jshell"]
