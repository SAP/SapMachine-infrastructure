FROM fedora:latest

RUN dnf install -y \
    python3 \
    ca-certificates \
    fedora-packager \
    rpmdevtools \
    git

RUN useradd -ms /bin/bash jenkins -u 1002
