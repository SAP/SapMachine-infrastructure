FROM alpine:3.23

RUN wget -qO /etc/apk/keys/sapmachine-apk.rsa.pub https://dist.sapmachine.io/alpine/sapmachine-apk.rsa.pub && \
    echo "4444e47cabf35695f9406692848de191d3b7cbd47dcdc1ffb62f4f70aea06e89 /etc/apk/keys/sapmachine-apk.rsa.pub" | sha256sum -c - && \
    echo "https://dist.sapmachine.io/alpine" >> /etc/apk/repositories && \
    apk add sapmachine-25-jdk=25.0.2-r0

ENV JAVA_HOME=/usr/lib/jvm/java-25-sapmachine-jdk

CMD ["jshell"]
