FROM opensuse:leap

RUN zypper ref
RUN zypper --non-interactive in --no-recommends \
    rpm \
    rpmbuild \
    createrepo \
    ca-certificates \
    wget

RUN useradd -ms /bin/bash jenkins -u 1001
