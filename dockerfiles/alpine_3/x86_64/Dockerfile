FROM alpine:3.17

RUN apk update && apk upgrade && apk add \
alpine-sdk \
alsa-lib-dev \
autoconf \
bash \
ca-certificates \
cpio \
cups-dev \
curl \
file \
fontconfig-dev \
g++ \
gcc \
git \
libx11-dev \
libxext-dev \
libxrandr-dev \
libxrender-dev \
libxt-dev \
libxtst-dev \
linux-headers \
make \
python3 \
py3-pip \
sed \
sudo \
tar \
unzip \
wget \
zip

RUN adduser --shell /bin/bash --uid 1000 --disabled-password jenkinsa
RUN adduser --shell /bin/bash --uid 1001 --disabled-password jenkinsb
RUN adduser --shell /bin/bash --uid 1002 --disabled-password jenkinsc

# enable the users for abuild-keygen, this needs sudo or doas
RUN echo "jenkinsa ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/jenkinsa && chmod 0440 /etc/sudoers.d/jenkinsa
RUN echo "jenkinsb ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/jenkinsb && chmod 0440 /etc/sudoers.d/jenkinsb
RUN echo "jenkinsc ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/jenkinsc && chmod 0440 /etc/sudoers.d/jenkinsc

RUN pip3 install requests

ADD https://raw.githubusercontent.com/tstuefe/tinyreaper/master/tinyreaper.c /tmp
RUN gcc /tmp/tinyreaper.c -o /opt/tinyreaper && \
    chmod +x /opt/tinyreaper && \
    rm /tmp/tinyreaper.c
