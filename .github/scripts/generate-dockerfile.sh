#!/usr/bin/env bash
# ==============================================================================
# generate-dockerfile.sh
#
# Generates a Dockerfile for a given SapMachine major version, full version,
# GardenLinux minor version, and flavour (jdk, jdk-headless, jre, jre-headless).
#
# Usage:
#   ./generate-dockerfile.sh <sm_major> <sm_version> <gl_version> <flavour> <output_dir>
#
# The gl_version should be the full minor version (e.g. 1592.18) which is used
# as the exact Docker base image tag for reproducibility.
#
# Example:
#   ./generate-dockerfile.sh 21 21.0.12 1592.18 jdk /tmp/build
# ==============================================================================
set -euo pipefail

SM_MAJOR="${1:?Usage: $0 <sm_major> <sm_version> <gl_version> <flavour> <output_dir>}"
SM_VERSION="${2:?}"
GL_VERSION="${3:?}"
FLAVOUR="${4:?}"
OUTPUT_DIR="${5:?}"

mkdir -p "${OUTPUT_DIR}"

# Determine CMD based on flavour
if [[ "${FLAVOUR}" == jdk* ]]; then
  CMD='["jshell"]'
else
  CMD='["bash"]'
fi

cat > "${OUTPUT_DIR}/Dockerfile" <<EOF
FROM ghcr.io/gardenlinux/gardenlinux:${GL_VERSION}

ENV LANG=C.UTF-8
ENV JAVA_VERSION=${SM_VERSION}
ENV MALLOC_ARENA_MAX=1

ADD --chmod=644 --chown=root:root https://dist.sapmachine.io/debian/sapmachine.key /etc/apt/trusted.gpg.d/sapmachine.asc

RUN echo "deb https://dist.sapmachine.io/debian/\$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list && \\
    apt-get update && \\
    apt-get -y --no-install-recommends install sapmachine-${SM_MAJOR}-${FLAVOUR}=${SM_VERSION} && \\
    rm -rf /var/lib/apt/lists/* && \\
    java -XshowSettings:properties -version

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-${SM_MAJOR}

CMD ${CMD}
EOF

echo "Generated Dockerfile at ${OUTPUT_DIR}/Dockerfile"
