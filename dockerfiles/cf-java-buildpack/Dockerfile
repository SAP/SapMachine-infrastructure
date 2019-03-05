FROM ubuntu:14.04

RUN apt-get update && apt-get install -qq -y --no-install-recommends \
    git \
    wget \
    zip \
    unzip \
    curl \
    ca-certificates \
    autoconf \
    make \
    gcc \
    g++ \
    zlib1g-dev \
    openssl \
    libssl-dev

RUN useradd -ms /bin/bash jenkins -u 1002
RUN echo "jenkins    ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

WORKDIR /tmp
RUN wget https://cache.ruby-lang.org/pub/ruby/2.5/ruby-2.5.0.tar.gz
RUN tar xf ruby-2.5.0.tar.gz
WORKDIR /tmp/ruby-2.5.0
RUN ./configure
RUN make -j8 install
RUN rm -rf /tmp/ruby-2.5.0

RUN gem install bundler

USER jenkins
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV JBP_CONFIG_COMPONENTS='{jres: ["JavaBuildpack::Jre::SapMachineJRE"]}'
WORKDIR /
