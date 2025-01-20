FROM alpine:3.21

RUN wget -qO /etc/apk/keys/sapmachine-apk.rsa.pub https://dist.sapmachine.io/alpine/sapmachine-apk.rsa.pub \
    && echo "https://dist.sapmachine.io/alpine" >> /etc/apk/repositories \
    && apk add sapmachine-17-jdk=17.0.13-r0

ENV JAVA_HOME=/usr/lib/jvm/java-17-sapmachine-jdk

CMD ["jshell"]
