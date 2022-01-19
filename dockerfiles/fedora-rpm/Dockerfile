FROM fedora:34

RUN dnf install -y \
    python3 \
    pip3 \
    ca-certificates \
    fedora-packager \
    rpmdevtools \
    git

RUN useradd -ms /bin/bash jenkins -u 1002

RUN pip3 install requests
