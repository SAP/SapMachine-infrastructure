FROM gcr.io/distroless/java-base-debian11:debug-nonroot as distroless

FROM ubuntu as builder

RUN apt-get update && apt-get -y --no-install-recommends install ca-certificates wget

RUN dpkgArch="$(dpkg --print-architecture)"; \
    case "${dpkgArch}" in \
		'amd64') \
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-20.0.2/sapmachine-jdk-20.0.2_linux-x64_bin.tar.gz'; \
			;; \
		'arm64') \
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-20.0.2/sapmachine-jdk-20.0.2_linux-aarch64_bin.tar.gz'; \
			;; \
		'ppc64el') \
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-20.0.2/sapmachine-jdk-20.0.2_linux-ppc64le_bin.tar.gz'; \
			;; \
		*) echo >&2 "error: unsupported architecture '$dpkgArch'"; exit 1 ;; \
	esac; \
    wget -O sapmachine.tar.gz $url --progress=dot:giga

COPY --from=distroless / /distroless

RUN tar xzf sapmachine.tar.gz && \
    rm -rf /distroless/etc/java-20-openjdk /distroless/usr/lib/jvm/java-20-openjdk-amd64 && \
    mv sapmachine-jdk-20.0.2 /distroless/usr/lib/jvm/java-20-openjdk-amd64

FROM scratch
COPY --from=builder /distroless /

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/busybox
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV LANG=C.UTF-8
ENV JAVA_VERSION=20.0.2

ENTRYPOINT [ "/usr/bin/java", "-jar" ]
