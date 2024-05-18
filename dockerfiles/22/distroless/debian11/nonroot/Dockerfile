FROM gcr.io/distroless/java-base-debian11:nonroot as distroless

FROM ubuntu as builder

RUN apt-get update && apt-get -y --no-install-recommends install ca-certificates wget

RUN dpkgArch="$(dpkg --print-architecture)"; \
    case "${dpkgArch}" in \
		'amd64') \
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-22.0.1/sapmachine-jre-22.0.1_linux-x64_bin.tar.gz'; \
			;; \
		'arm64') \
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-22.0.1/sapmachine-jre-22.0.1_linux-aarch64_bin.tar.gz'; \
			;; \
		'ppc64el') \
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-22.0.1/sapmachine-jre-22.0.1_linux-ppc64le_bin.tar.gz'; \
			;; \
		*) echo >&2 "error: unsupported architecture '$dpkgArch'"; exit 1 ;; \
	esac; \
    wget -O sapmachine.tar.gz $url --progress=dot:giga

COPY --from=distroless / /distroless

RUN tar xzf sapmachine.tar.gz && \
    rm -rf /distroless/etc/java-22-openjdk /distroless/usr/lib/jvm/java-22-openjdk-amd64 && \
    mv sapmachine-jre-22.0.1 /distroless/usr/lib/jvm/java-22-openjdk-amd64

FROM scratch
COPY --from=builder /distroless /


ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV LANG=C.UTF-8
ENV JAVA_VERSION=22.0.1

ENTRYPOINT [ "/usr/bin/java", "-jar" ]
