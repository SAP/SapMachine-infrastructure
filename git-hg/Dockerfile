FROM ubuntu:16.04

RUN apt-get update \
&& apt-get install -qq -y --no-install-recommends \
git \
mercurial \
gcc \
ca-certificates \
python-dev \
python-setuptools \
libffi-dev

RUN easy_install hg-git
RUN echo "[extensions]\nhgext.bookmarks =\nhggit =" > /etc/mercurial/hgrc

RUN cd ~ && git clone https://github.com/abourget/git-hg-again && cp git-hg-again/githg.py  /usr/lib/git-core/git-hg
