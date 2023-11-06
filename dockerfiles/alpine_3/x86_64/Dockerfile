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

# create users and add to abuild group which already exists
RUN adduser --shell /bin/bash --uid 1000 --ingroup abuild --disabled-password jenkinse
RUN adduser --shell /bin/bash --uid 50050 --ingroup abuild --disabled-password jenkinsi

# enable the users for abuild-keygen, this needs sudo or doas
RUN echo "jenkinse ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/jenkinse && chmod 0440 /etc/sudoers.d/jenkinse
RUN echo "jenkinsi ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/jenkinsi && chmod 0440 /etc/sudoers.d/jenkinsi

# create apk cache location
RUN mkdir -p /var/cache/distfiles
RUN chmod a+w /var/cache/distfiles

# prepare the apk keys, precondition for running make-apk.py
# doas has problems so tell abuild-keygen to use sudo instead
ENV SUDO=sudo
RUN abuild-keygen -a -i -n

RUN pip3 install requests

ADD https://raw.githubusercontent.com/tstuefe/tinyreaper/master/tinyreaper.c /tmp
RUN gcc /tmp/tinyreaper.c -o /opt/tinyreaper && \
    chmod +x /opt/tinyreaper && \
    rm /tmp/tinyreaper.c
