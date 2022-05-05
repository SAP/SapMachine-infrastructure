FROM alpine:3.15

RUN apk update && apk upgrade && apk add \
bash \
cpio \
make \
gcc \
g++ \
autoconf \
file \
libx11-dev \
libxext-dev \
libxrender-dev \
libxtst-dev \
libxt-dev \
libxrandr-dev \
cups-dev \
alsa-lib-dev \
linux-headers \
zip \
wget \
git \
unzip \
sed \
tar \
fontconfig-dev \
ca-certificates \
curl \
graphviz \
python3 \
py3-pip \
apache-ant \
patch

RUN adduser --shell /bin/bash --uid 1000 --disabled-password jenkinsa
RUN adduser --shell /bin/bash --uid 1001 --disabled-password jenkinsb
RUN adduser --shell /bin/bash --uid 1002 --disabled-password jenkinsc

RUN pip3 install requests

RUN mkdir /tmp/tinyreaper
ADD https://raw.githubusercontent.com/tstuefe/tinyreaper/master/tinyreaper.c /tmp/tinyreaper
RUN gcc /tmp/tinyreaper/tinyreaper.c -o /opt/tinyreaper
RUN chmod +x /opt/tinyreaper

ENV PATH=${PATH}:/opt
